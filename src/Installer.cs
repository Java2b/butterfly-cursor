using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ButterflyCursor
{
    /// <summary>
    /// Per-user installation without admin rights: copies the exe to a folder the user picks,
    /// adds Start menu / desktop shortcuts and an entry in Settings → Apps so it can be uninstalled.
    /// </summary>
    static class Installer
    {
        public const string AppName = "Butterfly Cursor";
        public const string Version = "1.5";
        const string AppKey = @"Software\ButterflyCursor";
        const string UninstallKey = @"Software\Microsoft\Windows\CurrentVersion\Uninstall\ButterflyCursor";

        public static string DefaultDir
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Butterfly"); }
        }

        public static string InstalledDir
        {
            get
            {
                try { return Registry.GetValue(@"HKEY_CURRENT_USER\" + AppKey, "InstallDir", null) as string; }
                catch { return null; }
            }
        }

        static string StartMenuLink
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), AppName + ".lnk"); }
        }

        static string DesktopLink
        {
            get { return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), AppName + ".lnk"); }
        }

        static bool SamePath(string a, string b)
        {
            try { return string.Equals(Path.GetFullPath(a).TrimEnd('\\'), Path.GetFullPath(b).TrimEnd('\\'), StringComparison.OrdinalIgnoreCase); }
            catch { return false; }
        }

        /// <summary>True when this copy should offer to install itself instead of just running.</summary>
        /// <summary>After an update the new exe tells Settings → Apps its version.</summary>
        public static void RefreshVersion()
        {
            try
            {
                using (RegistryKey k = Registry.CurrentUser.OpenSubKey(UninstallKey, true))
                    if (k != null && (k.GetValue("DisplayVersion") as string) != Version) k.SetValue("DisplayVersion", Version);
            }
            catch { }
        }

        public static bool ShouldOffer()
        {
            string dir = InstalledDir;
            if (dir != null && SamePath(Path.Combine(dir, "Butterfly.exe"), Application.ExecutablePath)) return false;
            try { return Convert.ToInt32(Registry.GetValue(@"HKEY_CURRENT_USER\" + AppKey, "NoSetupPrompt", 0) ?? 0) == 0; }
            catch { return true; }
        }

        public static void DontAskAgain()
        {
            try { Registry.SetValue(@"HKEY_CURRENT_USER\" + AppKey, "NoSetupPrompt", 1, RegistryValueKind.DWord); } catch { }
        }

        /// <summary>Asks a running copy to quit and waits until it is gone (its exe can then be replaced).</summary>
        static void StopRunningCopy()
        {
            IntPtr wnd = Native.FindWindow(null, Overlay.WindowTitle);
            if (wnd == IntPtr.Zero) return;
            uint pid;
            Native.GetWindowThreadProcessId(wnd, out pid);
            Native.PostMessage(wnd, 0x0010 /* WM_CLOSE */, IntPtr.Zero, IntPtr.Zero);
            try
            {
                using (Process p = Process.GetProcessById((int)pid))
                    if (!p.WaitForExit(4000)) p.Kill();
            }
            catch { }
        }

        static void Shortcut(string link, string target)
        {
            Type shellType = Type.GetTypeFromProgID("WScript.Shell");
            object shell = Activator.CreateInstance(shellType);
            object sc = shellType.InvokeMember("CreateShortcut", BindingFlags.InvokeMethod, null, shell, new object[] { link });
            Type t = sc.GetType();
            t.InvokeMember("TargetPath", BindingFlags.SetProperty, null, sc, new object[] { target });
            t.InvokeMember("WorkingDirectory", BindingFlags.SetProperty, null, sc, new object[] { Path.GetDirectoryName(target) });
            t.InvokeMember("IconLocation", BindingFlags.SetProperty, null, sc, new object[] { target + ",0" });
            t.InvokeMember("Description", BindingFlags.SetProperty, null, sc, new object[] { L.T("Бабочка, которая летает за мышью") });
            t.InvokeMember("Save", BindingFlags.InvokeMethod, null, sc, null);
        }

        /// <summary>Copies the program into <paramref name="dir"/> and registers it; returns the installed exe.</summary>
        public static string Install(string dir, bool desktop, bool autostart)
        {
            Directory.CreateDirectory(dir);
            string exe = Path.Combine(dir, "Butterfly.exe");
            StopRunningCopy();
            if (!SamePath(exe, Application.ExecutablePath)) File.Copy(Application.ExecutablePath, exe, true);

            // bring along the pictures that sit next to this copy
            string srcPics = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "creatures");
            string dstPics = Path.Combine(dir, "creatures");
            if (Directory.Exists(srcPics) && !SamePath(srcPics, dstPics))
            {
                Directory.CreateDirectory(dstPics);
                foreach (string f in Directory.GetFiles(srcPics))
                {
                    string to = Path.Combine(dstPics, Path.GetFileName(f));
                    if (!File.Exists(to)) File.Copy(f, to);
                }
            }

            try { Shortcut(StartMenuLink, exe); } catch { }
            try
            {
                if (desktop) Shortcut(DesktopLink, exe);
                else if (File.Exists(DesktopLink)) File.Delete(DesktopLink);
            }
            catch { }

            long size = new FileInfo(exe).Length;
            if (Directory.Exists(dstPics)) foreach (string f in Directory.GetFiles(dstPics)) size += new FileInfo(f).Length;

            using (RegistryKey k = Registry.CurrentUser.CreateSubKey(UninstallKey))
            {
                k.SetValue("DisplayName", AppName);
                k.SetValue("DisplayVersion", Version);
                k.SetValue("DisplayIcon", "\"" + exe + "\",0");
                k.SetValue("Publisher", AppName);
                k.SetValue("InstallLocation", dir);
                k.SetValue("UninstallString", "\"" + exe + "\" --uninstall");
                k.SetValue("EstimatedSize", (int)(size / 1024), RegistryValueKind.DWord);
                k.SetValue("NoModify", 1, RegistryValueKind.DWord);
                k.SetValue("NoRepair", 1, RegistryValueKind.DWord);
            }
            using (RegistryKey k = Registry.CurrentUser.CreateSubKey(AppKey))
                k.SetValue("InstallDir", dir);

            using (RegistryKey k = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
            {
                if (autostart) k.SetValue("ButterflyCursor", "\"" + exe + "\"");
                else k.DeleteValue("ButterflyCursor", false);
            }
            return exe;
        }

        /// <summary>Removes the program: shortcuts, registry entries, settings and files.</summary>
        public static void Uninstall()
        {
            if (MessageBox.Show(L.T("Удалить «Бабочку» с компьютера? Будут удалены программа, её настройки и картинки из папки creatures."),
                    AppName, MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
                return;

            StopRunningCopy();
            string dir = InstalledDir ?? Path.GetDirectoryName(Application.ExecutablePath);

            try { File.Delete(StartMenuLink); } catch { }
            try { File.Delete(DesktopLink); } catch { }
            try
            {
                using (RegistryKey k = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run"))
                    k.DeleteValue("ButterflyCursor", false);
            }
            catch { }
            try { Registry.CurrentUser.DeleteSubKeyTree(@"Software\Classes\DesktopBackground\Shell\ButterflyCursor", false); } catch { }
            try { Registry.CurrentUser.DeleteSubKeyTree(UninstallKey, false); } catch { }
            try { Registry.CurrentUser.DeleteSubKeyTree(AppKey, false); } catch { }

            // the running exe cannot delete itself: a hidden cmd does it a moment after we exit.
            // Only our own files are removed; the folder itself goes only if it is then empty.
            string exe = Path.Combine(dir, "Butterfly.exe");
            string pics = Path.Combine(dir, "creatures");
            MessageBox.Show(L.T("«Бабочка» удалена."), AppName, MessageBoxButtons.OK, MessageBoxIcon.Information);
            try
            {
                // keeps trying for up to ~30 s until our exe is no longer locked, then deletes itself
                string script = Path.Combine(Path.GetTempPath(), "butterfly-uninstall.cmd");
                File.WriteAllText(script,
                    "@echo off\r\nset n=0\r\n:retry\r\ndel /f /q \"" + exe + "\" >nul 2>&1\r\n" +
                    "if exist \"" + exe + "\" (set /a n+=1 & if %n% lss 30 (ping -n 2 127.0.0.1 >nul & goto retry))\r\n" +
                    "rmdir /s /q \"" + pics + "\" >nul 2>&1\r\nrmdir \"" + dir + "\" >nul 2>&1\r\ndel \"%~f0\"\r\n",
                    System.Text.Encoding.Default);
                Process.Start(new ProcessStartInfo("cmd.exe", "/c \"" + script + "\"") { CreateNoWindow = true, UseShellExecute = false, WindowStyle = ProcessWindowStyle.Hidden });
            }
            catch { }
        }
    }

    /// <summary>The first-run window: install to a chosen folder, or just run this copy.</summary>
    sealed class SetupForm : Form
    {
        public bool RunPortable;
        readonly TextBox folder = new TextBox();

        public SetupForm()
        {
            Text = L.T("Бабочка — установка");
            Font = new Font("Segoe UI", 9.5f);
            BackColor = Color.White;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            AutoScaleMode = AutoScaleMode.Font;
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

            var panel = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, Location = new Point(16, 12) };
            Controls.Add(panel);

            panel.Controls.Add(new Label
            {
                Text = L.T("Бабочка, которая летает за мышью"), AutoSize = true,
                Font = new Font("Segoe UI", 13f, FontStyle.Bold), ForeColor = Color.FromArgb(30, 110, 200), Margin = new Padding(0, 0, 0, 8)
            });
            panel.Controls.Add(new Label { Text = L.T("Куда установить программу?"), AutoSize = true, Margin = new Padding(0, 0, 0, 4) });

            var row = new FlowLayoutPanel { AutoSize = true, WrapContents = false, Margin = new Padding(0) };
            folder.Width = 360;
            folder.Text = Installer.InstalledDir ?? Installer.DefaultDir;
            var browse = new Button { Text = L.T("Обзор…"), AutoSize = true, FlatStyle = FlatStyle.System };
            browse.Click += delegate
            {
                using (var dlg = new FolderBrowserDialog { Description = L.T("Куда установить программу?"), SelectedPath = folder.Text })
                {
                    if (dlg.ShowDialog(this) != DialogResult.OK) return;
                    // always use our own sub-folder, so uninstalling never touches anything else
                    string picked = dlg.SelectedPath;
                    folder.Text = Path.GetFileName(picked.TrimEnd('\\')).Equals("Butterfly", StringComparison.OrdinalIgnoreCase)
                        ? picked : Path.Combine(picked, "Butterfly");
                }
            };
            row.Controls.Add(folder);
            row.Controls.Add(browse);
            panel.Controls.Add(row);

            var desktop = new CheckBox { Text = L.T("Ярлык на рабочем столе"), Checked = true, AutoSize = true, Margin = new Padding(0, 10, 0, 0) };
            var auto = new CheckBox { Text = L.T("Запускать вместе с Windows"), Checked = true, AutoSize = true, Margin = new Padding(0, 2, 0, 0) };
            panel.Controls.Add(desktop);
            panel.Controls.Add(auto);
            panel.Controls.Add(new Label
            {
                Text = L.T("Программа появится в меню «Пуск» и в «Параметры → Приложения», откуда её можно удалить."),
                AutoSize = true, MaximumSize = new Size(460, 0), ForeColor = Color.DimGray, Margin = new Padding(0, 8, 0, 0)
            });

            var never = new CheckBox { Text = L.T("Больше не спрашивать"), AutoSize = true, Margin = new Padding(0, 12, 0, 0) };
            var buttons = new FlowLayoutPanel { AutoSize = true, WrapContents = false, Margin = new Padding(0, 6, 0, 0) };
            var install = new Button { Text = L.T("Установить"), AutoSize = true, FlatStyle = FlatStyle.System, MinimumSize = new Size(120, 30) };
            var portable = new Button { Text = L.T("Запустить без установки"), AutoSize = true, FlatStyle = FlatStyle.System, MinimumSize = new Size(120, 30) };
            install.Click += delegate
            {
                try
                {
                    Cursor = Cursors.WaitCursor;
                    string exe = Installer.Install(folder.Text.Trim(), desktop.Checked, auto.Checked);
                    Process.Start(exe);
                    Close();
                }
                catch (Exception ex)
                {
                    Cursor = Cursors.Default;
                    MessageBox.Show(this, L.T("Не получилось установить:") + "\n" + ex.Message, Text, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            };
            portable.Click += delegate
            {
                if (never.Checked) Installer.DontAskAgain();
                RunPortable = true;
                Close();
            };
            buttons.Controls.Add(install);
            buttons.Controls.Add(portable);
            panel.Controls.Add(never);
            panel.Controls.Add(buttons);
            AcceptButton = install;

            Size pref = panel.GetPreferredSize(Size.Empty);
            ClientSize = new Size(pref.Width + 32, pref.Height + 28);
        }
    }
}
