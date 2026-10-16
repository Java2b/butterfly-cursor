using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ButterflyCursor
{
    enum MoveStyle { Fly = 0, Crawl = 1, Slide = 2, Float = 3, Run = 4, Wave = 5 }

    /// <summary>Country flags from the flag-icons pack, stored as one atlas image in the exe.</summary>
    static class Flags
    {
        const int W = 128, H = 96, Cols = 16;
        public static readonly List<string> Codes = new List<string>(), Names = new List<string>();

        static Flags()
        {
            Assembly asm = Assembly.GetExecutingAssembly();
            using (var r = new StreamReader(asm.GetManifestResourceStream("flags.txt"), System.Text.Encoding.UTF8))
            {
                string line;
                while ((line = r.ReadLine()) != null)
                {
                    int bar = line.IndexOf('|');
                    if (bar <= 0) continue;
                    Codes.Add(line.Substring(0, bar));
                    Names.Add(line.Substring(bar + 1));
                }
            }
        }

        /// <summary>Default: the country Windows is set to, if we have its flag.</summary>
        public static string DefaultCode
        {
            get
            {
                try
                {
                    string c = System.Globalization.RegionInfo.CurrentRegion.TwoLetterISORegionName.ToLowerInvariant();
                    if (Codes.Contains(c)) return c;
                }
                catch { }
                return "uz";
            }
        }

        public static Bitmap Get(string code)
        {
            int i = Math.Max(0, Codes.IndexOf(code));
            using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream("flags.png"))
            using (var atlas = new Bitmap(s))
                return atlas.Clone(new Rectangle(i % Cols * W, i / Cols * H, W, H), System.Drawing.Imaging.PixelFormat.Format32bppArgb);
        }
    }

    /// <summary>One selectable creature: a built-in sprite or a PNG from the "creatures" folder.</summary>
    sealed class Creature
    {
        public string Id, Title, File;
        public MoveStyle DefaultStyle;

        public Bitmap Load()
        {
            if (Id == "flag") return Flags.Get(Cfg.FlagCode);
            if (File != null)
                using (var fs = new FileStream(File, FileMode.Open, FileAccess.Read))
                using (var tmp = new Bitmap(fs))
                    return new Bitmap(tmp);
            using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(Id + ".png"))
                return new Bitmap(s);
        }

        /// <summary>A picture several times wider than tall, made of square frames, is an animation strip.</summary>
        public static bool IsStrip(int w, int h) { return h > 0 && w >= 2 * h && w % h == 0; }

        static bool IsStrip(string file)
        {
            try
            {
                using (var fs = new FileStream(file, FileMode.Open, FileAccess.Read))
                using (Image img = Image.FromStream(fs, false, false))
                    return IsStrip(img.Width, img.Height);
            }
            catch { return false; }
        }

        public static string Folder
        {
            get { return Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "creatures"); }
        }

        public static List<Creature> All()
        {
            var list = new List<Creature>
            {
                new Creature { Id = "butterfly", Title = L.T("Бабочка"), DefaultStyle = MoveStyle.Fly },
                new Creature { Id = "beetle", Title = L.T("Жук"), DefaultStyle = MoveStyle.Crawl },
                new Creature { Id = "spider", Title = L.T("Паук"), DefaultStyle = MoveStyle.Crawl },
                new Creature { Id = "snail", Title = L.T("Улитка"), DefaultStyle = MoveStyle.Slide },
                new Creature { Id = "ninja", Title = L.T("Ниндзя"), DefaultStyle = MoveStyle.Run },
                new Creature { Id = "flag", Title = L.T("Флаг"), DefaultStyle = MoveStyle.Wave },
            };
            Importer.ConvertPending();      // JPGs dropped into the folder become PNGs first
            try
            {
                if (Directory.Exists(Folder))
                    foreach (string f in Directory.GetFiles(Folder, "*.png"))
                        list.Add(new Creature
                        {
                            Id = "file:" + Path.GetFileName(f).ToLowerInvariant(),
                            Title = Path.GetFileNameWithoutExtension(f),
                            File = f,
                            DefaultStyle = IsStrip(f) ? MoveStyle.Run : MoveStyle.Float
                        });
            }
            catch { }
            return list;
        }
    }

    static class Cfg
    {
        const string Key = @"Software\ButterflyCursor";
        const string RunKey = @"Software\Microsoft\Windows\CurrentVersion\Run";
        const string RunName = "ButterflyCursor";

        public static string CreatureId, Lang = "", FlagCode;
        public static int Size, Speed, IdleSec, DustAmount, DustSize, DustLife, DustBright, Aura, AuraRgb;
        public static bool GoHome, Dust, HideFullscreen, Rainbow;
        /// <summary>Dust colours chosen by the user (0xRRGGBB); ignored while Rainbow is on.</summary>
        public static List<int> Colors = new List<int>();
        public const int MaxColors = 12;

        public static event Action Changed;

        // ready-made palettes; the last two entries are "rainbow" and "whatever the user picked"
        public static readonly string[] PresetNames =
            { "Волшебная (разноцветная)", "Голубая", "Золотая", "Розовая", "Зелёная", "Радуга", "Свои цвета" };
        public const int RainbowPreset = 5, CustomPreset = 6;

        public static List<int> Preset(int i)
        {
            var list = new List<int>();
            foreach (Color c in Themes[i]) list.Add(c.ToArgb() & 0xFFFFFF);
            return list;
        }

        /// <summary>Which ready-made palette the current colours are, or CustomPreset.</summary>
        public static int PresetIndex()
        {
            if (Rainbow) return RainbowPreset;
            for (int i = 0; i < Themes.Length; i++)
            {
                List<int> p = Preset(i);
                bool same = p.Count == Colors.Count;
                for (int j = 0; same && j < p.Count; j++) same = p[j] == Colors[j];
                if (same) return i;
            }
            return CustomPreset;
        }

        static readonly Color White = Color.FromArgb(255, 255, 255);
        static readonly Color[][] Themes =
        {
            new[] { Color.FromArgb(120, 220, 255), White, Color.FromArgb(255, 226, 140), Color.FromArgb(190, 160, 255), Color.FromArgb(90, 170, 255) },
            new[] { Color.FromArgb(120, 220, 255), White, Color.FromArgb(90, 170, 255) },
            new[] { Color.FromArgb(255, 226, 140), White, Color.FromArgb(255, 190, 80) },
            new[] { Color.FromArgb(255, 150, 210), White, Color.FromArgb(255, 110, 170) },
            new[] { Color.FromArgb(140, 255, 170), White, Color.FromArgb(60, 230, 140) },
        };

        public static void Defaults()
        {
            Size = 76; Speed = 5; IdleSec = 4; GoHome = true; HideFullscreen = true;
            Dust = true; DustAmount = 50; DustSize = 50; DustLife = 50; DustBright = 100;
            Colors = Preset(0); Rainbow = false; Aura = 0; AuraRgb = 0x78DCFF;
        }

        public static void Load()
        {
            Defaults();
            CreatureId = "butterfly";
            try { Load2(); } catch { }
            if (FlagCode == null || !Flags.Codes.Contains(FlagCode)) FlagCode = Flags.DefaultCode;
        }

        static void Load2()
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(Key))
                {
                    if (k == null) return;
                    CreatureId = Convert.ToString(k.GetValue("Creature", CreatureId));
                    Lang = Convert.ToString(k.GetValue("Lang", ""));
                    FlagCode = k.GetValue("Flag") as string;
                    Size = Int(k, "Size", Size, 24, 300);
                    Speed = Int(k, "Speed", Speed, 1, 10);
                    IdleSec = Int(k, "IdleSec", IdleSec, 1, 3600);
                    GoHome = Int(k, "GoHome", 1, 0, 1) == 1;
                    Dust = Int(k, "Dust", 1, 0, 1) == 1;
                    HideFullscreen = Int(k, "HideFullscreen", 1, 0, 1) == 1;
                    DustAmount = Int(k, "DustAmount", DustAmount, 0, 100);
                    DustSize = Int(k, "DustSize", DustSize, 0, 100);
                    DustLife = Int(k, "DustLife", DustLife, 0, 100);
                    DustBright = Int(k, "DustBright", DustBright, 10, 100);
                    Aura = Int(k, "Aura", Aura, 0, 100);

                    string saved = k.GetValue("Colors") as string;
                    if (saved != null)
                    {
                        var list = new List<int>();
                        foreach (string part in saved.Split(new[] { ',' }, StringSplitOptions.RemoveEmptyEntries))
                        {
                            int rgb;
                            if (list.Count < MaxColors && int.TryParse(part, System.Globalization.NumberStyles.HexNumber, null, out rgb))
                                list.Add(rgb & 0xFFFFFF);
                        }
                        if (list.Count > 0) Colors = list;
                        Rainbow = Int(k, "Rainbow", 0, 0, 1) == 1;
                        AuraRgb = Int(k, "AuraRgb", Colors[0], 0, 0xFFFFFF);
                    }
                    else
                    {
                        // settings saved by an older version: a theme number and one custom colour
                        int theme = Int(k, "Theme", 0, 0, 6), custom = Int(k, "CustomColor", 0x78DCFF, 0, 0xFFFFFF);
                        Rainbow = theme == 5;
                        if (theme == 6) Colors = new List<int> { custom, 0xFFFFFF };
                        else if (theme < 5) Colors = Preset(theme);
                        AuraRgb = Colors[0];
                    }
                }
            }
            catch { }
        }

        static int Int(RegistryKey k, string name, int def, int min, int max)
        {
            try { return Math.Max(min, Math.Min(max, Convert.ToInt32(k.GetValue(name, def)))); }
            catch { return def; }
        }

        /// <summary>Saves everything and tells the overlay to pick the changes up.</summary>
        public static void Apply()
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(Key))
                {
                    k.SetValue("Creature", CreatureId);
                    k.SetValue("Lang", Lang ?? "");
                    k.SetValue("Flag", FlagCode ?? "");
                    k.SetValue("Size", Size); k.SetValue("Speed", Speed); k.SetValue("IdleSec", IdleSec);
                    k.SetValue("GoHome", GoHome ? 1 : 0); k.SetValue("Dust", Dust ? 1 : 0);
                    k.SetValue("HideFullscreen", HideFullscreen ? 1 : 0);
                    k.SetValue("DustAmount", DustAmount); k.SetValue("DustSize", DustSize);
                    k.SetValue("DustLife", DustLife); k.SetValue("DustBright", DustBright);
                    k.SetValue("Aura", Aura); k.SetValue("AuraRgb", AuraRgb); k.SetValue("Rainbow", Rainbow ? 1 : 0);
                    k.SetValue("Colors", string.Join(",", Colors.ConvertAll(delegate(int c) { return c.ToString("X6"); }).ToArray()));
                }
            }
            catch { }
            if (Changed != null) Changed();
        }

        public static MoveStyle StyleOf(Creature c)
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(Key))
                    if (k != null) return (MoveStyle)Int(k, "Style." + c.Id, (int)c.DefaultStyle, 0, 5);
            }
            catch { }
            return c.DefaultStyle;
        }

        public static void SetStyle(Creature c, MoveStyle s)
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(Key))
                    k.SetValue("Style." + c.Id, (int)s);
            }
            catch { }
        }

        public static Color DustColor(Random rnd, double time)
        {
            if (Rainbow || Colors.Count == 0) return FromHue(((int)(time * 150) + rnd.Next(60)) / 15 * 15 % 360);
            return Color.FromArgb(255, Color.FromArgb(Colors[rnd.Next(Colors.Count)]));
        }

        public static Color AuraColor(double time)
        {
            if (Rainbow) return FromHue((int)(time * 40) / 15 * 15 % 360);
            return Color.FromArgb(255, Color.FromArgb(AuraRgb));
        }

        static Color FromHue(int h)
        {
            float x = 1 - Math.Abs(h / 60f % 2 - 1);
            float r = 0, g = 0, b = 0;
            if (h < 60) { r = 1; g = x; } else if (h < 120) { r = x; g = 1; }
            else if (h < 180) { g = 1; b = x; } else if (h < 240) { g = x; b = 1; }
            else if (h < 300) { r = x; b = 1; } else { r = 1; b = x; }
            // pastel, so the rainbow glows instead of looking like pure RGB
            return Color.FromArgb((int)(110 + 145 * r), (int)(110 + 145 * g), (int)(110 + 145 * b));
        }

        const string MenuKey = @"Software\Classes\DesktopBackground\Shell\ButterflyCursor";

        /// <summary>"Бабочка — настройки" item in the desktop right-click menu.</summary>
        public static bool DesktopMenu
        {
            get
            {
                try
                {
                    using (RegistryKey k = Registry.CurrentUser.OpenSubKey(Key))
                        return k == null || Int(k, "DesktopMenu", 1, 0, 1) == 1;
                }
                catch { return true; }
            }
            set
            {
                try
                {
                    using (RegistryKey k = Registry.CurrentUser.CreateSubKey(Key))
                        k.SetValue("DesktopMenu", value ? 1 : 0);
                }
                catch { }
                SyncDesktopMenu();
            }
        }

        /// <summary>Adds the menu item (pointing at wherever the exe is now) or removes it.</summary>
        public static void SyncDesktopMenu()
        {
            try
            {
                if (!DesktopMenu)
                {
                    Registry.CurrentUser.DeleteSubKeyTree(MenuKey, false);
                    return;
                }
                string exe = Application.ExecutablePath;
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(MenuKey))
                {
                    k.SetValue("MUIVerb", L.T("Бабочка — настройки"));
                    k.SetValue("Icon", "\"" + exe + "\"");
                    k.SetValue("Position", "Bottom");
                }
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(MenuKey + @"\command"))
                    k.SetValue("", "\"" + exe + "\" --settings");
            }
            catch { }
        }

        public static bool Autostart
        {
            get
            {
                try
                {
                    using (RegistryKey k = Registry.CurrentUser.OpenSubKey(RunKey))
                        return k != null && k.GetValue(RunName) != null;
                }
                catch { return false; }
            }
            set
            {
                try
                {
                    using (RegistryKey k = Registry.CurrentUser.CreateSubKey(RunKey))
                    {
                        if (value) k.SetValue(RunName, "\"" + Application.ExecutablePath + "\"");
                        else k.DeleteValue(RunName, false);
                    }
                }
                catch { }
            }
        }
    }
}
