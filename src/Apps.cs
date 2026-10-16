using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ButterflyCursor
{
    /// <summary>A program in which the creature hides while that program's window is the active one.</summary>
    sealed class AppRule
    {
        public string Title;
        public string[] Exes;       // process names, lower case, without ".exe"
        public bool On = true;
        public bool User;           // added by the user (can be removed)
    }

    static class Apps
    {
        const string Key = @"Software\ButterflyCursor";

        public static bool Enabled = true;
        /// <summary>0 = vanish, 1 = doze: shrink and sit by the Start button.</summary>
        public static int Mode = 1;
        public static List<AppRule> Rules = new List<AppRule>();

        static readonly HashSet<string> active = new HashSet<string>();
        static readonly Dictionary<uint, string> names = new Dictionary<uint, string>();
        static readonly uint ownPid = (uint)Process.GetCurrentProcess().Id;

        static List<AppRule> Standard()
        {
            return new List<AppRule>
            {
                Rule("Adobe Photoshop", "photoshop"),
                Rule("Adobe Illustrator", "illustrator"),
                Rule("Adobe Premiere Pro", "adobe premiere pro"),
                Rule("Adobe After Effects", "afterfx"),
                Rule("Adobe InDesign", "indesign"),
                Rule("Adobe Lightroom", "lightroom"),
                Rule("Zoom", "zoom"),
                Rule("Microsoft Word", "winword"),
                Rule("Microsoft Excel", "excel"),
                Rule("Microsoft PowerPoint", "powerpnt"),
                Rule("Microsoft Outlook", "outlook", "olk"),
                Rule("Microsoft Teams", "ms-teams", "teams"),
                Rule("Microsoft OneNote", "onenote"),
                Rule("Figma", "figma"),
                Rule("CorelDRAW", "coreldrw"),
                Rule("AutoCAD", "acad"),
                Rule("Blender", "blender"),
                Rule("DaVinci Resolve", "resolve"),
            };
        }

        static AppRule Rule(string title, params string[] exes)
        {
            return new AppRule { Title = title, Exes = exes };
        }

        public static void Load()
        {
            Rules = Standard();
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(Key))
                {
                    if (k != null)
                    {
                        Enabled = Convert.ToInt32(k.GetValue("ExcludeOn", 1)) != 0;
                        Mode = Convert.ToInt32(k.GetValue("ExcludeMode", 1)) == 0 ? 0 : 1;
                        var off = new HashSet<string>(Convert.ToString(k.GetValue("ExcludeOff", "")).Split(';'));
                        foreach (AppRule r in Rules) r.On = !off.Contains(r.Exes[0]);
                        foreach (string item in Convert.ToString(k.GetValue("ExcludeUser", "")).Split(';'))
                        {
                            string[] p = item.Split('|');
                            if (p.Length == 2 && p[0].Length > 0)
                                Rules.Add(new AppRule { Title = p[0], Exes = new[] { p[0] }, On = p[1] == "1", User = true });
                        }
                    }
                }
            }
            catch { }
            Rebuild();
        }

        public static void Save()
        {
            Rebuild();
            try
            {
                var off = new List<string>(); var user = new List<string>();
                foreach (AppRule r in Rules)
                {
                    if (r.User) user.Add(r.Exes[0] + "|" + (r.On ? "1" : "0"));
                    else if (!r.On) off.Add(r.Exes[0]);
                }
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(Key))
                {
                    k.SetValue("ExcludeOn", Enabled ? 1 : 0);
                    k.SetValue("ExcludeMode", Mode);
                    k.SetValue("ExcludeOff", string.Join(";", off.ToArray()));
                    k.SetValue("ExcludeUser", string.Join(";", user.ToArray()));
                }
            }
            catch { }
        }

        static void Rebuild()
        {
            active.Clear();
            if (!Enabled) return;
            foreach (AppRule r in Rules)
                if (r.On) foreach (string e in r.Exes) active.Add(e);
        }

        /// <summary>Adds a program by process name; returns false if it is already in the list.</summary>
        public static bool Add(string exe)
        {
            exe = Path.GetFileNameWithoutExtension(exe.Trim()).ToLowerInvariant();
            if (exe.Length == 0 || exe.IndexOf(';') >= 0 || exe.IndexOf('|') >= 0) return false;
            foreach (AppRule r in Rules)
                if (Array.IndexOf(r.Exes, exe) >= 0) { r.On = true; Save(); return false; }
            Rules.Add(new AppRule { Title = exe, Exes = new[] { exe }, User = true });
            Save();
            return true;
        }

        /// <summary>True while the active window belongs to one of the ticked programs.</summary>
        public static bool ForegroundExcluded()
        {
            if (active.Count == 0) return false;
            try
            {
                IntPtr fg = Native.GetForegroundWindow();
                if (fg == IntPtr.Zero) return false;
                uint pid;
                Native.GetWindowThreadProcessId(fg, out pid);
                if (pid == 0 || pid == ownPid) return false;
                string name;
                if (!names.TryGetValue(pid, out name))
                {
                    if (names.Count > 300) names.Clear();
                    using (Process p = Process.GetProcessById((int)pid)) name = p.ProcessName.ToLowerInvariant();
                    names[pid] = name;
                }
                return active.Contains(name);
            }
            catch { return false; }
        }
    }

    /// <summary>The list of programs in which the creature hides.</summary>
    sealed class AppsForm : Form
    {
        readonly CheckedListBox list = new CheckedListBox();
        readonly Button remove = new Button();
        bool loading;

        public AppsForm(Icon icon)
        {
            Text = L.T("Бабочка — программы");
            Icon = icon;
            Font = new Font("Segoe UI", 9f);
            BackColor = Color.White;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.CenterParent;
            AutoScaleMode = AutoScaleMode.Font;
            AutoSize = true;
            AutoSizeMode = AutoSizeMode.GrowAndShrink;
            Padding = new Padding(14, 10, 14, 12);

            var panel = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, AutoSize = true, WrapContents = false, Location = new Point(14, 10) };
            Controls.Add(panel);

            panel.Controls.Add(new Label
            {
                Text = L.T("Пока одна из отмеченных программ открыта и активна, существо уходит в сторону. Как только вы переключаетесь в другое окно, оно возвращается."),
                AutoSize = true, MaximumSize = new Size(400, 0), Margin = new Padding(3, 0, 3, 8)
            });

            var master = new CheckBox { Text = L.T("Прятаться в отмеченных программах"), AutoSize = true, Checked = Apps.Enabled, Margin = new Padding(3, 0, 3, 6) };
            master.CheckedChanged += delegate { Apps.Enabled = master.Checked; list.Enabled = master.Checked; Apps.Save(); };
            panel.Controls.Add(master);

            panel.Controls.Add(new Label { Text = L.T("Что делать в этих программах:"), AutoSize = true, Margin = new Padding(3, 4, 3, 2) });
            var doze = new RadioButton { Text = L.T("Стать неактивной: уменьшиться и сидеть у кнопки «Пуск»"), AutoSize = true, Checked = Apps.Mode == 1, Margin = new Padding(16, 0, 3, 0) };
            var vanish = new RadioButton { Text = L.T("Спрятаться: полностью исчезнуть"), AutoSize = true, Checked = Apps.Mode == 0, Margin = new Padding(16, 0, 3, 8) };
            doze.CheckedChanged += delegate { if (doze.Checked) { Apps.Mode = 1; Apps.Save(); } };
            vanish.CheckedChanged += delegate { if (vanish.Checked) { Apps.Mode = 0; Apps.Save(); } };
            panel.Controls.Add(doze);
            panel.Controls.Add(vanish);

            list.Size = new Size(400, 300);
            list.CheckOnClick = true;
            list.IntegralHeight = false;
            list.Enabled = Apps.Enabled;
            list.ItemCheck += delegate(object s, ItemCheckEventArgs e)
            {
                if (loading) return;
                Apps.Rules[e.Index].On = e.NewValue == CheckState.Checked;
                Apps.Save();
            };
            list.SelectedIndexChanged += delegate { remove.Enabled = list.SelectedIndex >= 0 && Apps.Rules[list.SelectedIndex].User; };
            panel.Controls.Add(list);

            var row = new FlowLayoutPanel { AutoSize = true, Margin = new Padding(0, 8, 0, 0) };
            var running = new Button { Text = L.T("Добавить запущенную программу…"), AutoSize = true, FlatStyle = FlatStyle.System };
            running.Click += delegate { ShowRunning(running); };
            var browse = new Button { Text = L.T("Выбрать файл программы…"), AutoSize = true, FlatStyle = FlatStyle.System };
            browse.Click += delegate
            {
                using (var dlg = new OpenFileDialog { Filter = L.T("Программы") + "|*.exe" })
                    if (dlg.ShowDialog(this) == DialogResult.OK) { Apps.Add(dlg.FileName); Fill(); }
            };
            row.Controls.Add(running);
            row.Controls.Add(browse);
            panel.Controls.Add(row);

            var row2 = new FlowLayoutPanel { AutoSize = true, Margin = new Padding(0, 4, 0, 0) };
            remove.Text = L.T("Удалить из списка");
            remove.AutoSize = true;
            remove.FlatStyle = FlatStyle.System;
            remove.Enabled = false;
            remove.Click += delegate
            {
                int i = list.SelectedIndex;
                if (i < 0 || !Apps.Rules[i].User) return;
                Apps.Rules.RemoveAt(i);
                Apps.Save();
                Fill();
            };
            var close = new Button { Text = L.T("Закрыть"), AutoSize = true, FlatStyle = FlatStyle.System, MinimumSize = new Size(90, 0) };
            close.Click += delegate { Close(); };
            row2.Controls.Add(remove);
            row2.Controls.Add(close);
            panel.Controls.Add(row2);
            AcceptButton = close;
            CancelButton = close;

            Fill();
        }

        void Fill()
        {
            loading = true;
            list.Items.Clear();
            foreach (AppRule r in Apps.Rules)
                list.Items.Add(r.User ? r.Title + ".exe  " + L.T("(добавлено вами)") : r.Title, r.On);
            loading = false;
            remove.Enabled = false;
        }

        /// <summary>Menu of the programs that have a window open right now.</summary>
        void ShowRunning(Control anchor)
        {
            var menu = new ContextMenuStrip();
            var seen = new HashSet<string> { "butterfly", "explorer", "applicationframehost", "textinputhost", "systemsettings", "shellexperiencehost", "searchhost", "startmenuexperiencehost" };
            foreach (Process p in Process.GetProcesses())
            {
                try
                {
                    if (p.MainWindowHandle == IntPtr.Zero || p.MainWindowTitle.Length == 0) continue;
                    string name = p.ProcessName;
                    if (!seen.Add(name.ToLowerInvariant())) continue;
                    string title = p.MainWindowTitle;
                    if (title.Length > 45) title = title.Substring(0, 45) + "…";
                    menu.Items.Add(name + "  —  " + title, null, delegate { Apps.Add(name); Fill(); });
                }
                catch { }
                finally { p.Dispose(); }
            }
            if (menu.Items.Count == 0) return;
            menu.Show(anchor, new Point(0, anchor.Height));
        }
    }
}
