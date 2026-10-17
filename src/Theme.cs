using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ButterflyCursor
{
    /// <summary>Light and dark colours for the program's windows.</summary>
    static class Theme
    {
        public static bool Dark { get { return Cfg.DarkTheme; } }

        public static Color Back { get { return Dark ? Color.FromArgb(30, 32, 40) : Color.White; } }
        public static Color Panel { get { return Dark ? Color.FromArgb(38, 41, 51) : Color.FromArgb(244, 246, 250); } }
        public static Color Card { get { return Dark ? Color.FromArgb(46, 49, 61) : Color.White; } }
        public static Color Border { get { return Dark ? Color.FromArgb(64, 68, 84) : Color.FromArgb(222, 226, 234); } }
        public static Color Text { get { return Dark ? Color.FromArgb(236, 238, 245) : Color.FromArgb(30, 32, 40); } }
        public static Color Sub { get { return Dark ? Color.FromArgb(150, 156, 172) : Color.FromArgb(110, 115, 130); } }
        public static Color Accent { get { return Dark ? Color.FromArgb(96, 158, 255) : Color.FromArgb(37, 110, 230); } }
        public static Color Sel { get { return Dark ? Color.FromArgb(45, 62, 102) : Color.FromArgb(232, 240, 255); } }
        public static Color StageTop { get { return Dark ? Color.FromArgb(22, 26, 44) : Color.FromArgb(234, 241, 255); } }
        public static Color StageBottom { get { return Dark ? Color.FromArgb(44, 52, 88) : Color.FromArgb(210, 224, 250); } }

        /// <summary>The colour scheme Windows uses for apps (first start only).</summary>
        public static bool SystemPrefersDark()
        {
            try
            {
                object v = Registry.GetValue(@"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 1);
                return v != null && Convert.ToInt32(v) == 0;
            }
            catch { return false; }
        }

        [DllImport("dwmapi.dll")] static extern int DwmSetWindowAttribute(IntPtr hwnd, int attr, ref int value, int size);
        [DllImport("uxtheme.dll", CharSet = CharSet.Unicode)] static extern int SetWindowTheme(IntPtr hwnd, string app, string idList);

        /// <summary>Colours a whole window: title bar, scroll bars, and every control by its kind.</summary>
        public static void Apply(Form form)
        {
            form.BackColor = Back;
            form.ForeColor = Text;
            form.HandleCreated += delegate { TitleBar(form); };
            if (form.IsHandleCreated) TitleBar(form);
            Style(form);
        }

        static void TitleBar(Form form)
        {
            int on = Dark ? 1 : 0;
            try
            {
                if (DwmSetWindowAttribute(form.Handle, 20, ref on, 4) != 0)       // Windows 11 / 10 20H1+
                    DwmSetWindowAttribute(form.Handle, 19, ref on, 4);            // older Windows 10
            }
            catch { }
        }

        static void Scrollbars(Control c)
        {
            Action set = delegate { try { SetWindowTheme(c.Handle, Dark ? "DarkMode_Explorer" : "Explorer", null); } catch { } };
            if (c.IsHandleCreated) set(); else c.HandleCreated += delegate { set(); };
        }

        static void Style(Control root)
        {
            foreach (Control c in root.Controls)
            {
                string tag = c.Tag as string;
                if (tag == "keep") continue;
                if (tag == "header") { c.ForeColor = Accent; c.BackColor = Color.Transparent; }
                else if (tag == "sub") c.ForeColor = Sub;
                else if (tag == "bar") c.BackColor = Panel;
                else if (c is LinkLabel)
                {
                    var l = (LinkLabel)c;
                    l.LinkColor = Accent; l.ActiveLinkColor = Accent; l.VisitedLinkColor = Accent;
                }
                else if (c is Label || c is CheckBox || c is RadioButton) { c.ForeColor = Text; c.BackColor = Color.Transparent; }
                else if (c is Button)
                {
                    var b = (Button)c;
                    if (tag != "swatch")
                    {
                        b.FlatStyle = FlatStyle.Flat;
                        b.UseVisualStyleBackColor = false;
                        b.BackColor = Card;
                        b.ForeColor = Text;
                        b.FlatAppearance.BorderColor = Border;
                        b.FlatAppearance.MouseOverBackColor = Sel;
                        b.Padding = new Padding(6, 2, 6, 2);
                    }
                }
                else if (c is ComboBox)
                {
                    var cb = (ComboBox)c;
                    cb.FlatStyle = FlatStyle.Standard;
                    cb.BackColor = Card; cb.ForeColor = Text;
                    // the native dark drop-down (Windows 10 1809+ / 11); light keeps the normal look
                    Action set = delegate { try { SetWindowTheme(cb.Handle, Dark ? "DarkMode_CFD" : "Explorer", null); } catch { } };
                    if (cb.IsHandleCreated) set(); else cb.HandleCreated += delegate { set(); };
                }
                else if (c is NumericUpDown || c is TextBox || c is RichTextBox || c is ListBox)
                {
                    c.BackColor = Card; c.ForeColor = Text;
                    if (c is ListBox || c is RichTextBox) Scrollbars(c);
                }
                else if (c is TrackBar) c.BackColor = Back;
                else if (c is ScrollableControl)
                {
                    c.BackColor = tag == "bar" ? Panel : Back;
                    if (((ScrollableControl)c).AutoScroll) Scrollbars(c);
                }
                if (c.HasChildren) Style(c);
            }
        }

        public static GraphicsPath Rounded(RectangleF r, float radius)
        {
            var p = new GraphicsPath();
            float d = Math.Min(radius * 2, Math.Min(r.Width, r.Height));
            if (d <= 0.5f) { p.AddRectangle(r); return p; }
            p.AddArc(r.X, r.Y, d, d, 180, 90);
            p.AddArc(r.Right - d, r.Y, d, d, 270, 90);
            p.AddArc(r.Right - d, r.Bottom - d, d, d, 0, 90);
            p.AddArc(r.X, r.Bottom - d, d, d, 90, 90);
            p.CloseFigure();
            return p;
        }
    }

    /// <summary>A small pill switch with a sun (light) and a moon (dark).</summary>
    sealed class ThemeToggle : Control
    {
        public event Action Toggled;

        public ThemeToggle()
        {
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint | ControlStyles.SupportsTransparentBackColor, true);
            Cursor = Cursors.Hand;
            Tag = "keep";
        }

        protected override void OnClick(EventArgs e)
        {
            base.OnClick(e);
            if (Toggled != null) Toggled();
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.Clear(Parent != null ? Parent.BackColor : Theme.Back);
            var r = new RectangleF(1, 1, Width - 3, Height - 3);
            using (GraphicsPath p = Theme.Rounded(r, r.Height / 2))
            using (var fill = new SolidBrush(Theme.Dark ? Color.FromArgb(52, 56, 72) : Color.FromArgb(232, 236, 244)))
            using (var pen = new Pen(Theme.Border))
            {
                g.FillPath(fill, p);
                g.DrawPath(pen, p);
            }
            float k = r.Height - 6;
            float kx = Theme.Dark ? r.Right - k - 3 : r.X + 3;
            var knob = new RectangleF(kx, r.Y + 3, k, k);
            using (var b = new SolidBrush(Theme.Accent)) g.FillEllipse(b, knob);
            float cx = knob.X + k / 2, cy = knob.Y + k / 2;
            if (Theme.Dark)
            {
                // crescent moon
                using (var w = new SolidBrush(Color.White)) g.FillEllipse(w, cx - k * 0.27f, cy - k * 0.27f, k * 0.54f, k * 0.54f);
                using (var a = new SolidBrush(Theme.Accent)) g.FillEllipse(a, cx - k * 0.12f, cy - k * 0.38f, k * 0.5f, k * 0.5f);
            }
            else
            {
                // sun with rays
                using (var w = new SolidBrush(Color.White)) g.FillEllipse(w, cx - k * 0.18f, cy - k * 0.18f, k * 0.36f, k * 0.36f);
                using (var pen = new Pen(Color.White, Math.Max(1.5f, k * 0.07f)))
                    for (int i = 0; i < 8; i++)
                    {
                        double a = i * Math.PI / 4;
                        g.DrawLine(pen, cx + (float)Math.Cos(a) * k * 0.27f, cy + (float)Math.Sin(a) * k * 0.27f,
                                        cx + (float)Math.Cos(a) * k * 0.38f, cy + (float)Math.Sin(a) * k * 0.38f);
                    }
            }
        }
    }
}
