using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Automation;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ButterflyCursor
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            try { Native.SetProcessDpiAwareness(2); }
            catch { try { Native.SetProcessDPIAware(); } catch { } }

            string[] args = Environment.GetCommandLineArgs();
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Cfg.Load();

            if (Array.IndexOf(args, "--uninstall") >= 0) { Installer.Uninstall(); return; }
            // a copy started from Downloads, a USB stick etc. first offers to install itself
            if (Array.IndexOf(args, "--settings") < 0 && Array.IndexOf(args, "--portable") < 0 && Installer.ShouldOffer())
            {
                var setup = new SetupForm();
                Application.Run(setup);
                if (!setup.RunPortable) return;
            }

            bool first;
            using (new Mutex(true, "ButterflyCursor.SingleInstance", out first))
            {
                if (!first)
                {
                    // already running: "Butterfly.exe --settings" just asks that copy to open its settings
                    if (Array.IndexOf(Environment.GetCommandLineArgs(), "--settings") >= 0)
                    {
                        IntPtr running = Native.FindWindow(null, Overlay.WindowTitle);
                        if (running != IntPtr.Zero)
                            Native.PostMessage(running, Native.ShowSettingsMessage, IntPtr.Zero, IntPtr.Zero);
                    }
                    return;
                }
                Apps.Load();
                Cfg.SyncDesktopMenu();
                if (Cfg.Autostart) Cfg.Autostart = true;     // keeps the autostart entry pointing at this exe
                Application.Run(new Overlay());
            }
        }
    }

    static class Native
    {
        public const int WS_EX_TOPMOST = 0x8, WS_EX_TRANSPARENT = 0x20, WS_EX_TOOLWINDOW = 0x80,
                         WS_EX_LAYERED = 0x80000, WS_EX_NOACTIVATE = 0x8000000;
        public const int ULW_ALPHA = 2;
        public static readonly IntPtr HWND_TOPMOST = new IntPtr(-1);
        public const int SWP_NOSIZE = 1, SWP_NOMOVE = 2, SWP_NOACTIVATE = 0x10;

        [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
        [StructLayout(LayoutKind.Sequential)] public struct SIZE { public int W, H; }
        [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        public struct BLENDFUNCTION { public byte Op, Flags, Alpha, Format; }
        [StructLayout(LayoutKind.Sequential)]
        public struct BITMAPINFOHEADER
        {
            public int biSize, biWidth, biHeight;
            public short biPlanes, biBitCount;
            public int biCompression, biSizeImage, biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant;
        }

        public static readonly int ShowSettingsMessage = RegisterWindowMessage("ButterflyCursor.ShowSettings");

        [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int RegisterWindowMessage(string name);
        [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd, int msg, IntPtr wp, IntPtr lp);
        [DllImport("shcore.dll")] public static extern int SetProcessDpiAwareness(int value);
        [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
        [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
        [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vk);
        [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr hwnd, int index);
        [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetClassName(IntPtr hwnd, System.Text.StringBuilder name, int max);
        [DllImport("shell32.dll")] public static extern int SHQueryUserNotificationState(out int state);
        [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string cls, string title);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindowEx(IntPtr parent, IntPtr after, string cls, string title);
        [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int cx, int cy, int flags);
        [DllImport("user32.dll")] public static extern bool DestroyIcon(IntPtr icon);
        [DllImport("user32.dll")]
        public static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr hdcDst, ref POINT dst, ref SIZE size,
            IntPtr hdcSrc, ref POINT src, int key, ref BLENDFUNCTION blend, int flags);
        [DllImport("kernel32.dll")] public static extern void RtlZeroMemory(IntPtr dst, IntPtr length);
        [DllImport("gdi32.dll")] public static extern IntPtr CreateCompatibleDC(IntPtr hdc);
        [DllImport("gdi32.dll")] public static extern bool DeleteDC(IntPtr hdc);
        [DllImport("gdi32.dll")] public static extern IntPtr SelectObject(IntPtr hdc, IntPtr obj);
        [DllImport("gdi32.dll")] public static extern bool DeleteObject(IntPtr obj);
        [DllImport("gdi32.dll")]
        public static extern IntPtr CreateDIBSection(IntPtr hdc, ref BITMAPINFOHEADER bmi, int usage, out IntPtr bits, IntPtr section, int offset);
    }

    /// <summary>32-bit premultiplied DIB that GDI+ draws into and UpdateLayeredWindow reads from.</summary>
    sealed class Surface : IDisposable
    {
        public IntPtr Dc, Bits;
        public Graphics G;
        public int W, H;
        IntPtr dib, oldObj;
        Bitmap bmp;

        public void Ensure(int w, int h)
        {
            if (w <= W && h <= H) return;
            int nw = Math.Max(W, (w + 255) / 256 * 256), nh = Math.Max(H, (h + 255) / 256 * 256);
            Dispose();
            W = nw; H = nh;
            var bi = new Native.BITMAPINFOHEADER();
            bi.biSize = Marshal.SizeOf(typeof(Native.BITMAPINFOHEADER));
            bi.biWidth = W; bi.biHeight = -H; bi.biPlanes = 1; bi.biBitCount = 32;
            Dc = Native.CreateCompatibleDC(IntPtr.Zero);
            dib = Native.CreateDIBSection(Dc, ref bi, 0, out Bits, IntPtr.Zero, 0);
            oldObj = Native.SelectObject(Dc, dib);
            bmp = new Bitmap(W, H, W * 4, PixelFormat.Format32bppPArgb, Bits);
            G = Graphics.FromImage(bmp);
            G.InterpolationMode = InterpolationMode.Bilinear;
            G.PixelOffsetMode = PixelOffsetMode.Half;
            G.SmoothingMode = SmoothingMode.AntiAlias;
        }

        public void Dispose()
        {
            if (G != null) { G.Dispose(); G = null; }
            if (bmp != null) { bmp.Dispose(); bmp = null; }
            if (Dc != IntPtr.Zero)
            {
                Native.SelectObject(Dc, oldObj);
                Native.DeleteObject(dib);
                Native.DeleteDC(Dc);
                Dc = IntPtr.Zero;
            }
            W = H = 0;
        }
    }

    sealed class Particle
    {
        public float X, Y, Vx, Vy, Life, MaxLife, Size, Phase, Rot, Spin;
        public int Rgb;
        public bool Star;
        public SeasonFx Kind;          // None = glowing dust; otherwise a snowflake, leaf, petal…
    }

    /// <summary>
    /// Finds the Start button of every taskbar (main one and the ones on extra monitors),
    /// for the Windows 11 XAML taskbar and the classic Windows 10 one.
    /// </summary>
    static class StartButton
    {
        /// <returns>Start button rectangle per monitor device name.</returns>
        public static Dictionary<string, Rectangle> FindAll()
        {
            var result = new Dictionary<string, Rectangle>();
            var trays = new List<IntPtr>();
            IntPtr main = Native.FindWindow("Shell_TrayWnd", null);
            if (main != IntPtr.Zero) trays.Add(main);
            IntPtr sec = IntPtr.Zero;
            while ((sec = Native.FindWindowEx(IntPtr.Zero, sec, "Shell_SecondaryTrayWnd", null)) != IntPtr.Zero)
                trays.Add(sec);

            foreach (IntPtr tray in trays)
            {
                Native.RECT wr;
                if (!Native.GetWindowRect(tray, out wr)) continue;
                Rectangle? r = FindIn(tray, wr);
                if (r == null) continue;
                string screen = Screen.FromRectangle(Rectangle.FromLTRB(wr.L, wr.T, wr.R, wr.B)).DeviceName;
                result[screen] = r.Value;
            }
            string fake = Environment.GetEnvironmentVariable("BUTTERFLY_TEST_START");
            if (!string.IsNullOrEmpty(fake))
            {
                string[] v = fake.Split(',');
                result[Screen.PrimaryScreen.DeviceName] = new Rectangle(int.Parse(v[0]), int.Parse(v[1]), int.Parse(v[2]), int.Parse(v[3]));
            }
            return result;
        }

        static Rectangle? FindIn(IntPtr tray, Native.RECT wr)
        {
            try
            {
                AutomationElement root = AutomationElement.FromHandle(tray);
                AutomationElement el = root.FindFirst(TreeScope.Descendants,
                    new PropertyCondition(AutomationElement.AutomationIdProperty, "StartButton"));
                if (el != null)
                {
                    System.Windows.Rect r = el.Current.BoundingRectangle;
                    if (!r.IsEmpty && r.Width > 4 && r.Height > 4)
                        return new Rectangle((int)r.X, (int)r.Y, (int)r.Width, (int)r.Height);
                }
            }
            catch { }

            Native.RECT sr;
            IntPtr start = Native.FindWindowEx(tray, IntPtr.Zero, "Start", null);
            if (start != IntPtr.Zero && Native.GetWindowRect(start, out sr) && sr.R - sr.L > 4)
                return Rectangle.FromLTRB(sr.L, sr.T, sr.R, sr.B);

            // Last resort: guess from the taskbar rectangle.
            int h = wr.B - wr.T;
            if (h <= 0 || h > wr.R - wr.L) return null;
            bool centered = false;
            try
            {
                int build = int.Parse((string)Registry.GetValue(
                    @"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion", "CurrentBuildNumber", "0"));
                object al = Registry.GetValue(
                    @"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl", 1);
                centered = build >= 22000 && (al == null || Convert.ToInt32(al) != 0);
            }
            catch { }
            int x = centered ? (wr.L + wr.R) / 2 - h / 2 : wr.L;
            return new Rectangle(x, wr.T, h, h);
        }
    }

    sealed class Overlay : Form
    {
        const int GlowLevels = 12;
        public const string WindowTitle = "ButterflyCursor.Overlay";   // how a second copy finds this one

        readonly Surface surface = new Surface();
        readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer();
        readonly Stopwatch clock = Stopwatch.StartNew();
        readonly Random rnd = new Random();
        readonly List<Particle> particles = new List<Particle>();
        readonly Dictionary<long, Bitmap> glow = new Dictionary<long, Bitmap>();
        readonly Pen starPen = new Pen(Color.White, 1f);
        readonly float dpi;
        NotifyIcon tray;
        Icon appIcon;
        SettingsForm settings;
        Bitmap source, sprite;
        Bitmap[] frames = new Bitmap[0];   // animation frames (a strip picture); frames[0] == sprite
        int runFrames = 1, idleFrame;
        RectangleF content;                // visible part of the sprite, for the flag pole
        Bitmap sitSprite;                  // resting pose (the ninja sitting on Start), if the creature has one
        static readonly ImageAttributes clampEdges = MakeClamp();

        static ImageAttributes MakeClamp()
        {
            var a = new ImageAttributes();
            a.SetWrapMode(WrapMode.TileFlipXY);
            return a;
        }
        string loadedId, shownLang;
        MoveStyle style;
        int S;

        // creature state
        float px, py, vx, vy, angle, phase, wing = 1f, facing = 1f, moving;
        bool resting, paused, wasIdle, fullscreen, dozing;

        public static Overlay Current;
        /// <summary>Demo mode for recording videos: flies figure eights on its own, ignoring the mouse.</summary>
        public bool Demo;
        public event Action DemoChanged;
        public void ToggleDemo() { Demo = !Demo; resting = false; if (DemoChanged != null) DemoChanged(); }

        // click reactions
        bool mouseWasDown;
        float hopT, flipT;
        readonly List<Shot> shots = new List<Shot>();
        // easter eggs: circles make it dizzy (then it sits on the pointer), shaking scares it away
        const float DizzyLen = 7f;
        float dizzyT, scaredT, circleAcc, lastMoveAngle = float.NaN;
        PointF scareTarget;
        Native.POINT prevCur;
        int lastShakeSign;
        readonly List<double> shakeTimes = new List<double>();
        // dancing to music
        readonly AudioMeter audio = new AudioMeter();
        float level, levelAvg, beat, lastPeak;
        double lastPeakRead;
        double lastBeat;
        // what the extra effects add to the drawing
        float funLift, spinDeg, pulse = 1f;
        SeasonFx[] seasonFx = new SeasonFx[0];
        double seasonChecked = -1000;
        float scale = 1f;      // < 1 while dozing by the Start button
        double lastFullscreenCheck;
        double last, lastMove, lastTopmost, lastStartLookup = -1000;
        Native.POINT lastCursor;
        float emitCarry;

        readonly object perchLock = new object();
        Dictionary<string, Rectangle> startRects = new Dictionary<string, Rectangle>();
        int lookupBusy;

        public Overlay()
        {
            Text = WindowTitle;
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            Location = new Point(-32000, -32000);
            Size = new Size(1, 1);

            using (Graphics g = Graphics.FromHwnd(IntPtr.Zero)) dpi = g.DpiX / 96f;

            Current = this;
            ApplySettings();
            BuildTray();
            Cfg.Changed += ApplySettings;

            Native.GetCursorPos(out lastCursor);
            px = lastCursor.X; py = lastCursor.Y;
            last = lastMove = clock.Elapsed.TotalSeconds;

            timer.Interval = 15;
            // a drawing glitch must never turn into an error window on the user's screen
            timer.Tick += delegate
            {
                try { Frame(); }
                catch (Exception ex)
                {
                    if (Environment.GetEnvironmentVariable("BUTTERFLY_DEBUG") == "1")
                        try { System.IO.File.AppendAllText(System.IO.Path.Combine(System.IO.Path.GetTempPath(), "butterfly-debug.txt"), ex + Environment.NewLine); } catch { }
                }
            };
            timer.Start();

            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--settings") >= 0)
                Shown += delegate { ShowSettings(); };
            // "Butterfly.exe --demo" starts straight in the demo mode (handy for recording)
            if (Array.IndexOf(Environment.GetCommandLineArgs(), "--demo") >= 0) Demo = true;
        }

        protected override bool ShowWithoutActivation { get { return true; } }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= Native.WS_EX_LAYERED | Native.WS_EX_TRANSPARENT | Native.WS_EX_TOOLWINDOW |
                              Native.WS_EX_TOPMOST | Native.WS_EX_NOACTIVATE;
                return cp;
            }
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == Native.ShowSettingsMessage) { ShowSettings(); return; }
            base.WndProc(ref m);
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            timer.Stop();
            if (tray != null) { tray.Visible = false; tray.Dispose(); }
            surface.Dispose();
            base.OnFormClosed(e);
        }

        // ---------- assets ----------

        void ApplySettings()
        {
            List<Creature> all = Creature.All();
            Creature c = all.Find(delegate(Creature x) { return x.Id == Cfg.CreatureId; }) ?? all[0];
            string want = c.Id == "flag" ? "flag:" + Cfg.FlagCode : c.Id;
            if (loadedId != want)
            {
                Bitmap loaded;
                try { loaded = c.Load(); }
                catch { c = all[0]; loaded = c.Load(); }
                if (source != null) source.Dispose();
                source = loaded;
                loadedId = want;
            }
            style = Cfg.StyleOf(c);
            resting = false;

            if (shownLang != L.Code)
            {
                bool first = shownLang == null;
                shownLang = L.Code;
                if (!first)
                {
                    // language switched: rebuild the menus and reopen the settings window in it
                    tray.Visible = false;
                    tray.Dispose();
                    BuildTray();
                    Cfg.SyncDesktopMenu();
                    if (settings != null && !settings.IsDisposed)
                        BeginInvoke((MethodInvoker)delegate { settings.Close(); settings = null; ShowSettings(); });
                }
            }

            S = Math.Max(24, (int)(Cfg.Size * dpi));
            // a strip of square frames is an animation; an odd number of frames means the last one is the idle pose
            int n = Creature.IsStrip(source.Width, source.Height) ? source.Width / source.Height : 1;
            idleFrame = n >= 3 && n % 2 == 1 ? n - 1 : 0;
            runFrames = idleFrame > 0 ? n - 1 : n;
            foreach (Bitmap old in frames) old.Dispose();
            frames = new Bitmap[n];
            int fw = source.Width / n;
            for (int i = 0; i < n; i++)
            {
                var b = new Bitmap(S, S, PixelFormat.Format32bppPArgb);
                using (Graphics g = Graphics.FromImage(b))
                {
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    // keep the picture's proportions inside the square sprite
                    float k = Math.Min((float)S / fw, (float)S / source.Height);
                    float w = fw * k, h = source.Height * k;
                    g.DrawImage(source, new RectangleF((S - w) / 2, (S - h) / 2, w, h), new RectangleF(i * fw, 0, fw, source.Height), GraphicsUnit.Pixel);
                    if (i == 0) content = new RectangleF((S - w) / 2, (S - h) / 2, w, h);
                }
                frames[i] = b;
            }
            sprite = frames[0];

            if (sitSprite != null) { sitSprite.Dispose(); sitSprite = null; }
            if (c.Id == "ninja")
                using (System.IO.Stream st = System.Reflection.Assembly.GetExecutingAssembly().GetManifestResourceStream("ninja_sit.png"))
                using (var sit = new Bitmap(st))
                {
                    sitSprite = new Bitmap(S, S, PixelFormat.Format32bppPArgb);
                    using (Graphics g = Graphics.FromImage(sitSprite))
                    {
                        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                        g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                        g.DrawImage(sit, 0, 0, S, S);
                    }
                }

            if (glow.Count > 4000)
            {
                foreach (Bitmap bmp in glow.Values) bmp.Dispose();
                glow.Clear();
            }
        }

        // Glow sprites are pre-rendered per colour / brightness / pixel size so that drawing
        // a dust particle is a plain unscaled blit.
        Bitmap Glow(int rgb, int lv, int size, bool aura)
        {
            long key = ((long)rgb << 24) | ((long)lv << 16) | ((long)size << 1) | (aura ? 1L : 0L);
            Bitmap cached;
            if (glow.TryGetValue(key, out cached)) return cached;

            int cr = (rgb >> 16) & 255, cg = (rgb >> 8) & 255, cb = rgb & 255;
            var bytes = new byte[size * size * 4];
            float half = size / 2f;
            for (int y = 0; y < size; y++)
                for (int x = 0; x < size; x++)
                {
                    float dx = (x + 0.5f - half) / half, dy = (y + 0.5f - half) / half;
                    float d2 = dx * dx + dy * dy;
                    float edge = Math.Max(0f, 1f - d2);
                    float core = aura ? 0f : (float)Math.Exp(-d2 * 60);
                    float halo = aura ? 0.75f * (float)Math.Exp(-d2 * 3.2) * edge : 0.5f * (float)Math.Exp(-d2 * 6) * edge;
                    float a = Math.Min(1f, core + halo) * lv / GlowLevels;
                    // the core burns to white, the halo keeps the dust colour
                    float r = cr + (255 - cr) * core, gr = cg + (255 - cg) * core, bl = cb + (255 - cb) * core;
                    int i = (y * size + x) * 4;
                    bytes[i] = (byte)(bl * a); bytes[i + 1] = (byte)(gr * a);
                    bytes[i + 2] = (byte)(r * a); bytes[i + 3] = (byte)(255 * a);
                }
            var bmp = new Bitmap(size, size, PixelFormat.Format32bppPArgb);
            BitmapData bd = bmp.LockBits(new Rectangle(0, 0, size, size), ImageLockMode.WriteOnly, PixelFormat.Format32bppPArgb);
            Marshal.Copy(bytes, 0, bd.Scan0, bytes.Length);
            bmp.UnlockBits(bd);
            glow[key] = bmp;
            return bmp;
        }

        // ---------- tray menu ----------

        void BuildTray()
        {
            using (Bitmap butterfly = new Creature { Id = "butterfly" }.Load())
            using (var small = new Bitmap(butterfly, 32, 32))
            {
                IntPtr h = small.GetHicon();
                appIcon = (Icon)Icon.FromHandle(h).Clone();
                Native.DestroyIcon(h);
            }

            var menu = new ContextMenuStrip();
            var open = new ToolStripMenuItem(L.T("Настройки…"));
            open.Font = new Font(open.Font, FontStyle.Bold);
            open.Click += delegate { ShowSettings(); };
            menu.Items.Add(open);

            var who = new ToolStripMenuItem(L.T("Существо"));
            menu.Items.Add(who);

            var demo = new ToolStripMenuItem(L.T("Демонстрация для видео")) { Checked = Demo };
            demo.Click += delegate { ToggleDemo(); };
            DemoChanged += delegate { demo.Checked = Demo; };
            menu.Items.Add(demo);

            var hide = new ToolStripMenuItem(L.T("Спрятать")) { CheckOnClick = true };
            hide.CheckedChanged += delegate { paused = hide.Checked; };
            menu.Items.Add(hide);

            menu.Items.Add(new ToolStripSeparator());
            menu.Items.Add(L.T("Выход"), null, delegate { Close(); });

            menu.Opening += delegate
            {
                who.DropDownItems.Clear();
                foreach (Creature c in Creature.All())
                {
                    Creature pick = c;
                    var item = new ToolStripMenuItem(c.Title) { Checked = c.Id == loadedId };
                    item.Click += delegate { Cfg.CreatureId = pick.Id; Cfg.Apply(); };
                    who.DropDownItems.Add(item);
                }
            };

            tray = new NotifyIcon { Icon = appIcon, Text = L.T("Бабочка — правый клик: настройки"), ContextMenuStrip = menu, Visible = true };
            tray.MouseClick += delegate(object s, MouseEventArgs e) { if (e.Button == MouseButtons.Left) ShowSettings(); };
        }

        void ShowSettings()
        {
            if (settings == null || settings.IsDisposed) settings = new SettingsForm(appIcon);
            settings.Show();
            if (settings.WindowState == FormWindowState.Minimized) settings.WindowState = FormWindowState.Normal;
            settings.Activate();
        }

        // ---------- simulation ----------

        void RefreshStartRects(double now, double minGap)
        {
            if (now - lastStartLookup < minGap) return;
            if (Interlocked.Exchange(ref lookupBusy, 1) == 1) return;
            lastStartLookup = now;
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    Dictionary<string, Rectangle> found = StartButton.FindAll();
                    lock (perchLock) startRects = found;
                }
                catch { }
                finally { Interlocked.Exchange(ref lookupBusy, 0); }
            });
        }

        /// <summary>Resting place: by the Start button of the monitor the mouse pointer is on.</summary>
        PointF Perch(out float wantScale)
        {
            Screen screen = Screen.FromPoint(new Point(lastCursor.X, lastCursor.Y));
            Rectangle s;
            bool found;
            lock (perchLock) found = startRects.TryGetValue(screen.DeviceName, out s);
            Rectangle b = screen.Bounds, wa = screen.WorkingArea;
            // which side the taskbar is on: where the working area is smaller than the screen
            bool top = wa.Top > b.Top, left = wa.Left > b.Left, right = wa.Right < b.Right;
            bool vertical = left || right;

            wantScale = 1f;
            float size = S;
            if (dozing)
            {
                // asleep: shrinks to the size of the Start icon
                size = found ? Math.Min(s.Width, s.Height) * 0.8f : 32f * dpi;
                wantScale = Math.Min(1f, size / S);
            }

            PointF p;
            if (!found)
                p = new PointF(wa.Left + wa.Width / 2f, wa.Bottom - size * 0.5f);
            else if (dozing)
            {
                // right next to the icon itself (about 0.4 of the taskbar thickness, in the middle of the button);
                // on the left side if there is room, otherwise on the right (Windows 10: Start in the corner)
                float cx = s.Left + s.Width / 2f, cy = s.Top + s.Height / 2f;
                if (vertical)
                    p = new PointF(cx, cy + s.Width * 0.2f + size * 0.42f);
                else
                {
                    float icon = s.Height * 0.2f;
                    p = new PointF(cx - icon - size * 0.42f, cy);
                    if (p.X - size / 2 < b.Left) p = new PointF(cx + icon + size * 0.42f, cy);
                }
            }
            else if (sitSprite != null)
            {
                // the ninja sits right on top of the Start button
                float cx = s.Left + s.Width / 2f;
                p = top ? new PointF(cx, s.Bottom + S * 0.45f) : new PointF(cx, s.Top + s.Height * 0.42f - S * 0.40f);
            }
            else
            {
                // side-view creatures stand on the taskbar edge; the others sit on it
                float lift = style == MoveStyle.Slide ? 0.30f : style == MoveStyle.Float ? 0.40f
                           : style == MoveStyle.Run ? 0.46f : style == MoveStyle.Wave ? 0.48f : 0.12f;
                if (left) p = new PointF(s.Right + S * 0.5f, s.Top + s.Height / 2f);
                else if (right) p = new PointF(s.Left - S * 0.5f, s.Top + s.Height / 2f);
                else if (top) p = new PointF(s.Left + s.Width * 0.25f, s.Bottom + S * lift);
                else p = new PointF(s.Left + s.Width * 0.25f, s.Top - S * lift);
            }

            // never leave the screen (Start in the very corner, small screens, big creatures)
            float h = size / 2;
            p.X = Math.Max(b.Left + h, Math.Min(b.Right - h, p.X));
            p.Y = Math.Max(b.Top + h * 0.5f, Math.Min(b.Bottom - h * 0.5f, p.Y));
            return p;
        }

        /// <summary>True when the active window is a game / video covering its whole monitor.</summary>
        static bool FullscreenAppActive()
        {
            try
            {
                int state;
                if (Native.SHQueryUserNotificationState(out state) == 0 && state == 3) return true;   // exclusive Direct3D

                IntPtr fg = Native.GetForegroundWindow();
                if (fg == IntPtr.Zero) return false;
                uint pid;
                Native.GetWindowThreadProcessId(fg, out pid);
                if (pid == (uint)Process.GetCurrentProcess().Id) return false;

                var cls = new System.Text.StringBuilder(64);
                Native.GetClassName(fg, cls, 64);
                string c = cls.ToString();
                if (c == "Progman" || c == "WorkerW" || c == "Shell_TrayWnd" || c == "Shell_SecondaryTrayWnd") return false;

                Native.RECT r;
                if (!Native.GetWindowRect(fg, out r)) return false;
                Rectangle m = Screen.FromHandle(fg).Bounds;
                if (r.L > m.Left || r.T > m.Top || r.R < m.Right || r.B < m.Bottom) return false;
                // a maximized ordinary window (title bar, hangs over the edges) is not full screen
                bool exact = r.L == m.Left && r.T == m.Top && r.R == m.Right && r.B == m.Bottom;
                bool caption = (Native.GetWindowLong(fg, -16) & 0xC00000) == 0xC00000;
                return exact || !caption;
            }
            catch { return false; }
        }

        float Rand(float a, float b) { return a + (float)rnd.NextDouble() * (b - a); }

        void Emit(float x, float y, float bvx, float bvy, double now)
        {
            if (particles.Count >= 700) return;
            float sizeK = 0.4f + Cfg.DustSize / 50f * 0.6f, lifeK = 0.4f + Cfg.DustLife / 50f * 0.6f;
            var p = new Particle();
            p.X = x + Rand(-1, 1) * S * 0.12f;
            p.Y = y + Rand(-1, 1) * S * 0.12f;
            p.Vx = bvx * 0.06f + Rand(-28, 28) * dpi;
            p.Vy = bvy * 0.06f + Rand(-28, 14) * dpi;
            p.MaxLife = p.Life = Rand(0.6f, 1.5f) * lifeK;
            p.Size = Rand(1.0f, 2.4f) * dpi * (0.75f + S / (150f * dpi)) * sizeK;
            p.Phase = Rand(0, 6.28f);
            p.Rgb = Cfg.DustColor(rnd, now).ToArgb() & 0xFFFFFF;
            p.Star = rnd.Next(4) == 0;
            if (Cfg.Seasons && seasonFx.Length > 0 && rnd.Next(10) < 4)
            {
                // snowflakes, leaves, petals, confetti, pumpkins: bigger, slower, tumbling
                p.Kind = seasonFx[rnd.Next(seasonFx.Length)];
                p.Size = Rand(5f, 9f) * dpi * sizeK * (p.Kind == SeasonFx.Pumpkins ? 1.3f : 1f);
                p.MaxLife = p.Life = Rand(1.6f, 2.8f) * lifeK;
                p.Vy = Rand(-25f, 10f) * dpi;
                p.Rot = Rand(0, 360);
                p.Spin = Rand(-200f, 200f);
                p.Rgb = rnd.Next(SeasonSprites.Variants);
            }
            particles.Add(p);
        }

        /// <summary>A ring of sparks flying outwards (clicks, shuriken hits, beats, being scared).</summary>
        void Burst(float x, float y, int n, double now)
        {
            float sizeK = 0.4f + Cfg.DustSize / 50f * 0.6f;
            for (int i = 0; i < n && particles.Count < 700; i++)
            {
                float a = Rand(0, 6.2832f), v = Rand(150f, 420f) * dpi;
                var p = new Particle();
                p.X = x; p.Y = y;
                p.Vx = (float)Math.Cos(a) * v; p.Vy = (float)Math.Sin(a) * v;
                p.MaxLife = p.Life = Rand(0.45f, 0.9f);
                p.Size = Rand(1.2f, 2.6f) * dpi * sizeK * 1.2f;
                p.Phase = Rand(0, 6.28f);
                p.Rgb = Cfg.DustColor(rnd, now).ToArgb() & 0xFFFFFF;
                p.Star = rnd.Next(3) == 0;
                particles.Add(p);
            }
        }

        /// <summary>Clicks, the two easter eggs and the music meter.</summary>
        void UpdateFun(Native.POINT cur, double now, float dt)
        {
            bool visible = !paused && !dozing;

            // clicks: polling the left button, no mouse hook needed
            // bit 0x8000 = held now; bit 1 = pressed since the last check (catches very short clicks)
            short state = Native.GetAsyncKeyState(0x01);
            bool down = (state & 0x8000) != 0;
            bool clicked = !mouseWasDown && (down || (state & 1) != 0);
            if (clicked && visible && Cfg.ClickFx)
            {
                Burst(cur.X, cur.Y, 18, now);
                if (sitSprite != null && !resting)
                {
                    // the ninja throws a shuriken at the spot
                    float sx = px, sy = py - S * 0.1f, ddx = cur.X - sx, ddy = cur.Y - sy;
                    float len = Math.Max(1f, (float)Math.Sqrt(ddx * ddx + ddy * ddy)), v = 1600f * dpi;
                    shots.Add(new Shot { X = sx, Y = sy, Vx = ddx / len * v, Vy = ddy / len * v, Life = len / v });
                }
                else if (style == MoveStyle.Fly || style == MoveStyle.Float || style == MoveStyle.Wave || style == MoveStyle.Crawl) flipT = 0.6f;
                else hopT = 0.45f;
            }
            mouseWasDown = down;
            if (hopT > 0) hopT = Math.Max(0, hopT - dt);
            if (flipT > 0) flipT = Math.Max(0, flipT - dt);

            for (int i = shots.Count - 1; i >= 0; i--)
            {
                Shot sh = shots[i];
                sh.X += sh.Vx * dt; sh.Y += sh.Vy * dt; sh.Rot += 1080f * dt; sh.Life -= dt;
                if (sh.Life <= 0) { Burst(sh.X, sh.Y, 14, now); shots.RemoveAt(i); }
            }

            // easter eggs, from how the pointer moves
            float mx = cur.X - prevCur.X, my = cur.Y - prevCur.Y;
            prevCur = cur;
            float step = (float)Math.Sqrt(mx * mx + my * my);
            if (step > 4f * dpi && dt > 0)
            {
                float ang = (float)Math.Atan2(my, mx);
                if (!float.IsNaN(lastMoveAngle))
                {
                    float d = ang - lastMoveAngle;
                    while (d > Math.PI) d -= 6.2832f;
                    while (d < -Math.PI) d += 6.2832f;
                    if (Math.Abs(d) < 1.3f) circleAcc += d; else circleAcc *= 0.5f;
                }
                lastMoveAngle = ang;

                if (step / dt > 1800f * dpi && Math.Abs(mx) > Math.Abs(my))
                {
                    int sign = Math.Sign(mx);
                    // drawing circles also flips left/right all the time; only count it when not circling
                    if (lastShakeSign != 0 && sign != lastShakeSign && Math.Abs(circleAcc) < 6.2832f) shakeTimes.Add(now);
                    lastShakeSign = sign;
                }
            }
            circleAcc *= 1f - Math.Min(1f, dt * 0.6f);
            shakeTimes.RemoveAll(delegate(double x) { return now - x > 1.2; });

            if (Math.Abs(circleAcc) > 6.2832f * 4f && dizzyT <= 0 && scaredT <= 0 && visible)
            {
                dizzyT = DizzyLen;
                circleAcc = 0;
            }
            if (shakeTimes.Count >= 6 && scaredT <= 0 && visible)
            {
                // flees to the far side of the screen for a moment
                Rectangle b = Screen.FromPoint(new Point(cur.X, cur.Y)).Bounds;
                scareTarget = new PointF(cur.X < b.Left + b.Width / 2 ? b.Right - S : b.Left + S, b.Top + b.Height * 0.3f);
                scaredT = 2.5f;
                dizzyT = 0;
                shakeTimes.Clear();
                Burst(px, py, 24, now);
            }
            if (dizzyT > 0) dizzyT = Math.Max(0, dizzyT - dt);
            if (scaredT > 0) scaredT = Math.Max(0, scaredT - dt);

            // music: follow the speaker level, a "beat" is a jump well above the recent average
            // the meter is read 20 times a second, not every frame: plenty for dancing, lighter on the audio service
            if (now - lastPeakRead > 0.05) { lastPeakRead = now; lastPeak = Cfg.Music && visible ? audio.Peak(now) : 0f; }
            float peak = lastPeak;
            level += (peak - level) * Math.Min(1f, dt * 12f);
            levelAvg += (peak - levelAvg) * Math.Min(1f, dt * 1.5f);
            if (peak > 0.06f && peak > levelAvg * 1.45f && now - lastBeat > 0.28)
            {
                lastBeat = now;
                beat = 1f;
                if (Cfg.Dust) Burst(px, py, 6, now);
            }
            beat = Math.Max(0f, beat - dt * 4f);

            // what all of this does to the creature on screen
            float hop = hopT > 0 ? (float)Math.Sin(Math.PI * (1 - hopT / 0.45f)) : 0f;
            funLift = S * (0.35f * hop + 0.12f * beat);
            spinDeg = 0f;
            if (flipT > 0) spinDeg = 360f * (1f - flipT / 0.6f);
            if (dizzyT > DizzyLen - 1.2f) spinDeg = (float)(now * 900 % 360);
            pulse = 1f + 0.08f * level;
        }

        void Frame()
        {
            double now = clock.Elapsed.TotalSeconds;
            float dt = (float)Math.Min(0.05, now - last);
            last = now;
            float t = (float)now;

            if (now - lastFullscreenCheck > 0.4)
            {
                lastFullscreenCheck = now;
                bool fs = Cfg.HideFullscreen && FullscreenAppActive();
                bool inApp = Apps.ForegroundExcluded();
                // listed programs: either vanish completely or doze, small, by the Start button
                fullscreen = fs || (inApp && Apps.Mode == 0);
                dozing = inApp && Apps.Mode == 1 && !fs;
            }
            if (fullscreen)
            {
                // a game, a full-screen video or a program from the "hide in" list is in front:
                // stay out of the way and do nothing
                particles.Clear();
                timer.Interval = 250;
                Render(t);
                return;
            }

            if (now - lastTopmost > 2)
            {
                lastTopmost = now;
                Native.SetWindowPos(Handle, Native.HWND_TOPMOST, 0, 0, 0, 0,
                    Native.SWP_NOMOVE | Native.SWP_NOSIZE | Native.SWP_NOACTIVATE);
            }

            Native.POINT cur;
            if (!Native.GetCursorPos(out cur)) cur = lastCursor;
            if (Math.Abs(cur.X - lastCursor.X) + Math.Abs(cur.Y - lastCursor.Y) > 1)
            {
                lastMove = now;
                lastCursor = cur;
            }
            if (now - seasonChecked > 600)
            {
                seasonChecked = now;
                seasonFx = Season.Current();
            }
            UpdateFun(cur, now, dt);
            bool idle = dozing || (Cfg.GoHome && now - lastMove > Cfg.IdleSec);
            // the demo and the easter eggs keep it busy even when the mouse rests
            if (!dozing && (Demo || dizzyT > 0 || scaredT > 0)) idle = false;
            RefreshStartRects(now, idle && !wasIdle ? 3 : 120);
            wasIdle = idle;

            // speed setting 1..10; crawlers are slower than fliers, the snail is much slower
            float styleK = style == MoveStyle.Crawl ? 0.65f : style == MoveStyle.Slide ? 0.2f : style == MoveStyle.Run ? 0.85f : 1f;
            float maxSpeed = 180f * Cfg.Speed * dpi * styleK;
            float arrive = 2f + 0.6f * Cfg.Speed;

            float tx, ty, wantScale = 1f;
            if (idle)
            {
                PointF perch = Perch(out wantScale);
                tx = perch.X; ty = perch.Y;
            }
            else if (Demo)
            {
                // a big, slow figure eight over the middle of the main screen
                Rectangle wa = Screen.PrimaryScreen.WorkingArea;
                tx = wa.Left + wa.Width / 2f + (float)Math.Sin(t * 0.55f) * wa.Width * 0.33f;
                ty = wa.Top + wa.Height * 0.45f + (float)Math.Sin(t * 1.1f) * wa.Height * 0.25f;
                resting = false;
            }
            else if (scaredT > 0)
            {
                tx = scareTarget.X; ty = scareTarget.Y;
                maxSpeed *= 2.2f; arrive *= 2f;
                resting = false;
            }
            else if (dizzyT > 0 && dizzyT <= DizzyLen - 1.2f)
            {
                // tired and dizzy: sits right on the tip of the pointer and rides along
                tx = cur.X; ty = cur.Y - S * 0.32f;
                maxSpeed *= 2f; arrive *= 4f;
                resting = false;
            }
            else
            {
                // stay beside the pointer, not on top of it; fliers also hover around a little
                tx = cur.X + S * 0.62f; ty = cur.Y + S * 0.55f;
                if (style == MoveStyle.Fly || style == MoveStyle.Float || style == MoveStyle.Wave)
                {
                    tx += (float)Math.Sin(t * 1.7f) * S * 0.22f;
                    ty += (float)Math.Sin(t * 2.3f + 1f) * S * 0.18f;
                }
                resting = false;
            }
            scale += (wantScale - scale) * Math.Min(1f, dt * 3f);

            float dx = tx - px, dy = ty - py;
            float dist = (float)Math.Sqrt(dx * dx + dy * dy);
            float speed = (float)Math.Sqrt(vx * vx + vy * vy);

            if (idle && !resting && dist < 3f * dpi && speed < 40f * dpi) resting = true;
            if (resting && dist > 6f * dpi) resting = false;      // taskbar moved or other monitor

            float moved = 0;
            if (resting)
            {
                px = tx; py = ty; vx = vy = 0; speed = 0;
            }
            else
            {
                // steer towards the target: full speed far away, slowing down on arrival,
                // with limited acceleration so that take-off is not a sudden jump
                float wantSpeed = Math.Min(maxSpeed, dist * arrive);
                float wx = dist > 0.01f ? dx / dist * wantSpeed : 0, wy = dist > 0.01f ? dy / dist * wantSpeed : 0;
                float ax = (wx - vx) * 7f, ay = (wy - vy) * 7f;
                float acc = (float)Math.Sqrt(ax * ax + ay * ay), maxAcc = maxSpeed * 3.5f;
                if (acc > maxAcc) { ax *= maxAcc / acc; ay *= maxAcc / acc; }
                vx += ax * dt; vy += ay * dt;
                float ox = px, oy = py;
                px += vx * dt; py += vy * dt;
                moved = (float)Math.Sqrt((px - ox) * (px - ox) + (py - oy) * (py - oy));
                speed = (float)Math.Sqrt(vx * vx + vy * vy);
            }

            float target = Math.Min(1f, speed / Math.Max(1f, maxSpeed * 0.45f));
            moving += (target - moving) * Math.Min(1f, dt * 8f);
            if (Math.Abs(vx) > 12f * dpi) facing = vx > 0 ? 1f : -1f;

            // heading: nose points where it goes
            bool turning = speed > (style == MoveStyle.Fly ? 70f : 12f) * dpi;
            float want;
            if (style == MoveStyle.Float || style == MoveStyle.Wave || style == MoveStyle.Run)
            {
                // stays upright, only leans a little into the direction of flight
                turning = false;
                want = Math.Max(-14f, Math.Min(14f, vx / Math.Max(1f, maxSpeed) * 14f));
            }
            else if (turning) want = (float)(Math.Atan2(vx, -vy) * 180 / Math.PI);
            else if (style == MoveStyle.Fly) want = resting ? 14f : 9f * (float)Math.Sin(t * 1.3f);
            else want = resting ? 0f : angle;
            float da = ((want - angle) % 360f + 540f) % 360f - 180f;
            angle += da * Math.Min(1f, dt * (turning ? 9f : 4f));

            // animation clock: wing beats / leg wiggle / snail stretching
            float freq;
            bool riding = dizzyT > 0 && dizzyT <= DizzyLen - 1.2f;
            if (style == MoveStyle.Fly) freq = resting || riding ? 0.33f : 5f + 5f * moving + 6f * level;
            else if (style == MoveStyle.Crawl) freq = 6.5f * moving;
            else if (style == MoveStyle.Float) freq = resting ? 0f : 0.9f;
            else if (style == MoveStyle.Run) freq = 2.6f * moving;              // full run cycles per second
            else if (style == MoveStyle.Wave) freq = 0.8f + 1.4f * moving;
            else freq = 1.6f * moving;
            phase += dt * freq * 6.2832f;
            float wantWing = resting || riding
                ? 0.80f + 0.20f * (float)Math.Cos(phase)
                : 0.56f + 0.44f * (float)Math.Cos(phase);
            wing += (wantWing - wing) * Math.Min(1f, dt * 30f);

            // fairy dust
            if (!paused && !dozing && Cfg.Dust && Cfg.DustAmount > 0)
            {
                float tailX, tailY;
                if (style == MoveStyle.Slide || style == MoveStyle.Run) { tailX = px - facing * S * 0.3f; tailY = py + S * 0.2f; }
                else
                {
                    float rad = angle * (float)Math.PI / 180f;
                    tailX = px - (float)Math.Sin(rad) * S * 0.22f; tailY = py + (float)Math.Cos(rad) * S * 0.22f;
                }
                float amount = Cfg.DustAmount / 50f;
                float still = resting ? 0.8f : (style == MoveStyle.Fly || style == MoveStyle.Float || style == MoveStyle.Wave ? 5f : 0.8f);
                emitCarry += (moved / (6f * dpi) + dt * still) * amount;
                while (emitCarry >= 1f)
                {
                    emitCarry -= 1f;
                    if (speed < 1f) Emit(px + Rand(-1, 1) * S * 0.35f, py + Rand(-1, 1) * S * 0.3f, 0, -200f * dpi, now);
                    else Emit(tailX, tailY, -vx, -vy, now);
                }
            }

            for (int i = particles.Count - 1; i >= 0; i--)
            {
                Particle p = particles[i];
                p.Life -= dt;
                if (p.Life <= 0) { particles.RemoveAt(i); continue; }
                if (p.Kind == SeasonFx.None)
                {
                    p.Vy += 38f * dpi * dt;
                    p.Vx *= 1f - 1.6f * dt; p.Vy *= 1f - 1.6f * dt;
                }
                else
                {
                    // drifts down slowly, swaying from side to side and tumbling
                    p.Vy += (45f * dpi - p.Vy) * Math.Min(1f, dt * 1.5f);
                    p.Vx += ((float)Math.Sin(p.Phase + p.Life * 2.6f) * 40f * dpi - p.Vx) * Math.Min(1f, dt * 2f);
                    p.Rot += p.Spin * dt;
                }
                p.X += p.Vx * dt; p.Y += p.Vy * dt;
            }

            bool busy = shots.Count > 0 || hopT > 0 || flipT > 0 || beat > 0 || level > 0.02f || dizzyT > 0;
            timer.Interval = speed < 1f && !busy ? 40 : 15;
            Render(t);
        }

        // ---------- drawing ----------

        void Render(float t)
        {
            float r = S * (AuraNow > 0 ? 1.05f : 0.80f) * pulse + funLift;
            float minX = px - r, minY = py - r, maxX = px + r, maxY = py + r;
            foreach (Particle p in particles)
            {
                float pr = p.Size * 9f;
                if (p.X - pr < minX) minX = p.X - pr;
                if (p.Y - pr < minY) minY = p.Y - pr;
                if (p.X + pr > maxX) maxX = p.X + pr;
                if (p.Y + pr > maxY) maxY = p.Y + pr;
            }
            foreach (Shot sh in shots)
            {
                float pr = S * 0.3f;
                minX = Math.Min(minX, sh.X - pr); minY = Math.Min(minY, sh.Y - pr);
                maxX = Math.Max(maxX, sh.X + pr); maxY = Math.Max(maxY, sh.Y + pr);
            }
            Rectangle box = Rectangle.FromLTRB((int)Math.Floor(minX), (int)Math.Floor(minY),
                                               (int)Math.Ceiling(maxX), (int)Math.Ceiling(maxY));
            // snap to a coarse grid so the window is not resized on every frame
            const int Grid = 128;
            box = Rectangle.FromLTRB(FloorTo(box.Left, Grid), FloorTo(box.Top, Grid),
                                     FloorTo(box.Right + Grid - 1, Grid), FloorTo(box.Bottom + Grid - 1, Grid));
            box.Intersect(SystemInformation.VirtualScreen);
            if (paused || fullscreen || box.Width <= 0 || box.Height <= 0) box = new Rectangle(box.X, box.Y, 1, 1);

            surface.Ensure(box.Width, box.Height);
            Graphics g = surface.G;
            g.ResetTransform();
            g.Flush();
            Native.RtlZeroMemory(surface.Bits, new IntPtr((long)surface.W * 4 * box.Height));

            if (!paused && !fullscreen)
            {
                g.TranslateTransform(-box.X, -box.Y);
                if (AuraNow > 0) DrawAura(g, t);
                foreach (Particle p in particles) DrawParticle(g, p, t);
                foreach (Shot sh in shots) DrawShot(g, sh);
                DrawCreature(g);
                if (dizzyT > 0) DrawDizzyStars(g, t);
            }
            g.Flush();

            var dst = new Native.POINT { X = box.X, Y = box.Y };
            var size = new Native.SIZE { W = box.Width, H = box.Height };
            var src = new Native.POINT();
            var blend = new Native.BLENDFUNCTION { Op = 0, Flags = 0, Alpha = 255, Format = 1 };
            Native.UpdateLayeredWindow(Handle, IntPtr.Zero, ref dst, ref size, surface.Dc, ref src, 0, ref blend, Native.ULW_ALPHA);
        }

        static int FloorTo(int v, int grid) { return (int)Math.Floor(v / (double)grid) * grid; }

        bool NightNow { get { return Cfg.NightGlow && Season.Night; } }

        /// <summary>Glow around the creature: the setting, but at least a soft one at night.</summary>
        int AuraNow { get { return NightNow ? Math.Max(Cfg.Aura, 45) : Cfg.Aura; } }

        void DrawShot(Graphics g, Shot sh)
        {
            GraphicsState st = g.Save();
            g.TranslateTransform(sh.X, sh.Y);
            g.RotateTransform(sh.Rot);
            float r = Math.Max(6f, S * 0.12f);
            var pts = new PointF[8];
            for (int i = 0; i < 8; i++)
            {
                double a = i * Math.PI / 4;
                float rr = i % 2 == 0 ? r : r * 0.35f;
                pts[i] = new PointF((float)Math.Cos(a) * rr, (float)Math.Sin(a) * rr);
            }
            using (var glow = new SolidBrush(Color.FromArgb(70, 150, 210, 255))) g.FillEllipse(glow, -r * 1.4f, -r * 1.4f, r * 2.8f, r * 2.8f);
            using (var br = new SolidBrush(Color.FromArgb(210, 220, 235))) g.FillPolygon(br, pts);
            using (var pen = new Pen(Color.FromArgb(60, 70, 90), 1.2f)) g.DrawPolygon(pen, pts);
            using (var hole = new SolidBrush(Color.FromArgb(60, 70, 90))) g.FillEllipse(hole, -r * 0.15f, -r * 0.15f, r * 0.3f, r * 0.3f);
            g.Restore(st);
        }

        /// <summary>Little stars circling above the head of a dizzy creature.</summary>
        void DrawDizzyStars(Graphics g, float t)
        {
            float cx = px, cy = py - S * 0.5f * scale, rx = S * 0.28f * scale, ry = S * 0.08f * scale;
            float r = Math.Max(3f, S * 0.05f);
            using (var br = new SolidBrush(Color.FromArgb(255, 235, 120)))
                for (int i = 0; i < 3; i++)
                {
                    double a = t * 5 + i * 2.094;
                    float x = cx + (float)Math.Cos(a) * rx, y = cy + (float)Math.Sin(a) * ry;
                    var pts = new PointF[10];
                    for (int k = 0; k < 10; k++)
                    {
                        double b = k * Math.PI / 5 - Math.PI / 2;
                        float rr = k % 2 == 0 ? r : r * 0.45f;
                        pts[k] = new PointF(x + (float)Math.Cos(b) * rr, y + (float)Math.Sin(b) * rr);
                    }
                    g.FillPolygon(br, pts);
                }
        }

        void DrawSeasonal(Graphics g, Particle p)
        {
            float f = p.Life / p.MaxLife;
            float a = (f < 0.35f ? f / 0.35f : 1f) * Math.Max(0.4f, Cfg.DustBright / 100f);
            Bitmap bmp = SeasonSprites.Get(p.Kind, p.Rgb, a);
            float d = p.Size * 2.2f;
            GraphicsState st = g.Save();
            g.TranslateTransform(p.X, p.Y);
            g.RotateTransform(p.Rot);
            g.DrawImage(bmp, -d / 2, -d / 2, d, d);
            g.Restore(st);
        }

        void DrawAura(Graphics g, float t)
        {
            float pulse = 0.85f + 0.15f * (float)Math.Sin(t * 2.2f);
            int lv = (int)(AuraNow / 100f * pulse * GlowLevels + 0.5f);
            if (lv < 1) return;
            int d = Math.Max(16, Math.Min(1400, (int)(S * 2f * scale) & ~15));
            g.DrawImageUnscaled(Glow(Cfg.AuraColor(t).ToArgb() & 0xFFFFFF, Math.Min(GlowLevels, lv), d, true),
                (int)Math.Round(px) - d / 2, (int)Math.Round(py) - d / 2);
        }

        void DrawParticle(Graphics g, Particle p, float t)
        {
            float f = p.Life / p.MaxLife;
            float fade = f < 0.7f ? f / 0.7f : 1f;
            float twinkle = 0.72f + 0.28f * (float)Math.Sin(p.Phase + t * 17f);
            if (p.Kind != SeasonFx.None) { DrawSeasonal(g, p); return; }
            float a = Math.Min(1f, fade * twinkle * Cfg.DustBright / 100f * (NightNow ? 1.25f : 1f));
            int lv = (int)(a * GlowLevels + 0.5f);
            if (lv < 1) return;
            if (lv > GlowLevels) lv = GlowLevels;

            int d = Math.Min(1023, Math.Max(4, (int)(p.Size * 15f * (0.55f + 0.45f * f)) & ~1));
            g.DrawImageUnscaled(Glow(p.Rgb, lv, d, false), (int)Math.Round(p.X) - d / 2, (int)Math.Round(p.Y) - d / 2);

            if (p.Star)
            {
                float len = p.Size * 4.2f * twinkle * (0.4f + 0.6f * f);
                starPen.Color = Color.FromArgb((int)(210 * a), 255, 255, 255);
                starPen.Width = Math.Max(1f, dpi * 0.9f);
                g.DrawLine(starPen, p.X - len, p.Y, p.X + len, p.Y);
                g.DrawLine(starPen, p.X, p.Y - len, p.X, p.Y + len);
            }
        }

        /// <summary>Hop, flip, dizzy spin and the music pulse, on top of the normal pose.</summary>
        void ApplyFun(Graphics g)
        {
            if (funLift != 0) g.TranslateTransform(0, -funLift);
            if (spinDeg != 0) g.RotateTransform(spinDeg);
            if (pulse != 1f) g.ScaleTransform(pulse, pulse);
        }

        void DrawCreature(Graphics g)
        {
            GraphicsState state = g.Save();
            float half = S / 2f;

            if (style == MoveStyle.Fly)
            {
                // a tiny bob in time with the wing beat makes the flight feel alive
                float bob = resting ? 0f : (float)Math.Sin(phase) * S * 0.035f;
                g.TranslateTransform(px, py + bob);
                g.ScaleTransform(scale, scale);
                ApplyFun(g);
                g.RotateTransform(angle);

                float body = S * 0.035f;            // half-width of the body strip that never folds
                float wingW = half - body;
                float w = wingW * wing;

                // wings fold around the body axis: left and right halves squeezed horizontally
                g.DrawImage(sprite, new RectangleF(-body - w, -half, w + 0.5f, S),
                            new RectangleF(0, 0, wingW + 0.5f, S), GraphicsUnit.Pixel);
                g.DrawImage(sprite, new RectangleF(body - 0.5f, -half, w + 0.5f, S),
                            new RectangleF(half + body - 0.5f, 0, wingW + 0.5f, S), GraphicsUnit.Pixel);
                g.DrawImage(sprite, new RectangleF(-body, -half, body * 2, S),
                            new RectangleF(half - body, 0, body * 2, S), GraphicsUnit.Pixel);
            }
            else if (style == MoveStyle.Float)
            {
                // upright picture that bobs gently in the air
                g.TranslateTransform(px, py + (float)Math.Sin(phase) * S * 0.05f);
                g.ScaleTransform(scale, scale);
                ApplyFun(g);
                g.RotateTransform(angle);
                g.DrawImage(sprite, -half, -half, S, S);
            }
            else if (style == MoveStyle.Run)
            {
                // side view, frame-by-frame run cycle; the idle pose when standing still
                int idx = idleFrame;
                if (moving > 0.12f && runFrames > 0)
                    idx = ((int)(phase / 6.2832f * runFrames) % runFrames + runFrames) % runFrames;
                g.TranslateTransform(px, py);
                g.ScaleTransform(scale, scale);
                ApplyFun(g);
                if (resting && sitSprite != null)
                {
                    // sitting in meditation: slow breathing
                    float breath = 1f + 0.018f * (float)Math.Sin(clock.Elapsed.TotalSeconds * 1.6);
                    g.DrawImage(sitSprite, -half, half - S * breath, S, S * breath);
                }
                else
                {
                    g.ScaleTransform(facing, 1f);
                    g.DrawImage(frames[Math.Min(idx, frames.Length - 1)], -half, -half, S, S);
                }
            }
            else if (style == MoveStyle.Wave)
            {
                // a flag on a pole: the cloth is drawn in thin slices that ripple more towards the free end
                g.TranslateTransform(px, py);
                g.ScaleTransform(scale, scale);
                ApplyFun(g);
                g.RotateTransform(angle * 0.5f);
                float left = -half + content.X, top = -half + content.Y;
                float pole = Math.Max(2f, S * 0.025f);
                using (var pen = new Pen(Color.FromArgb(235, 205, 130), pole))
                    g.DrawLine(pen, left - pole / 2, top - pole, left - pole / 2, half);
                using (var ball = new SolidBrush(Color.FromArgb(255, 225, 150)))
                    g.FillEllipse(ball, left - pole * 1.5f, top - pole * 3f, pole * 2f, pole * 2f);
                int slices = Math.Max(12, (int)(content.Width / 3));
                float sw = content.Width / slices, amp = content.Height * 0.06f * (0.6f + moving);
                bool shade = loadedId.StartsWith("flag:");
                for (int i = 0; i < slices; i++)
                {
                    float k = (float)i / slices, wave = phase - k * 13f;
                    float dy = (float)Math.Sin(wave) * amp * k;
                    float x = left + i * sw, y = top + dy;
                    // the edge-clamping attributes stop see-through seams between the slices
                    g.DrawImage(sprite, new[] { new PointF(x, y), new PointF(x + sw + 0.5f, y), new PointF(x, y + content.Height) },
                                new RectangleF(content.X + i * sw, content.Y, sw, content.Height), GraphicsUnit.Pixel, clampEdges);
                    if (shade)
                    {
                        // light and shadow on the folds
                        float light = (float)Math.Cos(wave) * k;
                        using (var br = new SolidBrush(light > 0 ? Color.FromArgb((int)(light * 40), 255, 255, 255) : Color.FromArgb((int)(-light * 55), 0, 0, 0)))
                            g.FillRectangle(br, x, y, sw + 0.5f, content.Height);
                    }
                }
            }
            else if (style == MoveStyle.Crawl)
            {
                // waddle from side to side while walking
                float s = (float)Math.Sin(phase);
                g.TranslateTransform(px, py);
                g.ScaleTransform(scale, scale);
                ApplyFun(g);
                g.RotateTransform(angle + 7f * s * moving);
                float w = S * (1f + 0.04f * s * moving), h = S * (1f - 0.04f * s * moving);
                g.DrawImage(sprite, -w / 2, -h / 2, w, h);
            }
            else
            {
                // side view: stretches and squeezes along the ground, turns by mirroring
                float s = (float)Math.Sin(phase) * moving;
                g.TranslateTransform(px, py);
                g.ScaleTransform(scale, scale);
                ApplyFun(g);
                g.ScaleTransform(facing, 1f);
                float w = S * (1f + 0.07f * s), h = S * (1f - 0.05f * s);
                g.DrawImage(sprite, -w / 2, half - h, w, h);
            }
            g.Restore(state);
        }
    }
}
