using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;
using Microsoft.Win32;

namespace ButterflyCursor
{
    /// <summary>
    /// Looks for a newer release on GitHub (at most every 12 hours) and offers it:
    /// "Yes" downloads the new exe, swaps it in and restarts; "No" asks again in 12 hours.
    /// </summary>
    static class Updater
    {
        const string Api = "https://api.github.com/repos/Java2b/butterfly-cursor/releases/latest";
        public const string Page = "https://github.com/Java2b/butterfly-cursor/releases/latest";
        const string Key = @"HKEY_CURRENT_USER\Software\ButterflyCursor";
        static readonly TimeSpan Pause = TimeSpan.FromHours(12);

        static System.Windows.Forms.Timer timer;
        static int busy;
        static UpdateForm shown;

        /// <summary>First look shortly after start, then every half hour (each look respects the 12 hour pause).</summary>
        public static void Start(Control ui)
        {
            timer = new System.Windows.Forms.Timer { Interval = 20000 };
            timer.Tick += delegate { timer.Interval = 30 * 60 * 1000; Check(ui, false); };
            timer.Start();
        }

        static DateTime NextLook
        {
            get
            {
                try { return new DateTime(Convert.ToInt64(Registry.GetValue(Key, "UpdateNextLook", "0") ?? "0"), DateTimeKind.Utc); }
                catch { return DateTime.MinValue; }
            }
            set { try { Registry.SetValue(Key, "UpdateNextLook", value.Ticks.ToString()); } catch { } }
        }

        /// <param name="now">true: look right away (ignores the pause and the setting).</param>
        public static void Check(Control ui, bool now)
        {
            if (!now && (!Cfg.CheckUpdates || DateTime.UtcNow < NextLook)) return;
            if (shown != null && !shown.IsDisposed) return;
            if (Interlocked.Exchange(ref busy, 1) == 1) return;
            ThreadPool.QueueUserWorkItem(delegate
            {
                try
                {
                    Release r = Latest();
                    if (r != null && IsNewer(r.Version, Installer.Version))
                        ui.BeginInvoke((MethodInvoker)delegate { Ask(r); });
                    else
                    {
                        NextLook = DateTime.UtcNow + Pause;
                        if (now) ui.BeginInvoke((MethodInvoker)delegate
                        {
                            MessageBox.Show(L.T("У вас последняя версия.") + " (" + Installer.Version + ")", L.T("Бабочка"), MessageBoxButtons.OK, MessageBoxIcon.Information);
                        });
                    }
                }
                catch { NextLook = DateTime.UtcNow + TimeSpan.FromHours(1); }   // offline: try again later
                finally { Interlocked.Exchange(ref busy, 0); }
            });
        }

        sealed class Release { public string Version, ExeUrl; public long Size; }

        static WebClient Client()
        {
            // GitHub needs TLS 1.2 and a user agent
            try { ServicePointManager.SecurityProtocol |= (SecurityProtocolType)3072; } catch { }
            var wc = new WebClient();
            wc.Headers[HttpRequestHeader.UserAgent] = "ButterflyCursor/" + Installer.Version;
            return wc;
        }

        static Release Latest()
        {
            string json;
            using (WebClient wc = Client())
            {
                wc.Headers[HttpRequestHeader.Accept] = "application/vnd.github+json";
                json = wc.DownloadString(Api);
            }
            Match tag = Regex.Match(json, "\"tag_name\"\\s*:\\s*\"v?([0-9.]+)\"");
            Match exe = Regex.Match(json, "\"name\"\\s*:\\s*\"Butterfly\\.exe\".*?\"size\"\\s*:\\s*(\\d+).*?\"browser_download_url\"\\s*:\\s*\"([^\"]+)\"", RegexOptions.Singleline);
            if (!tag.Success || !exe.Success) return null;
            return new Release { Version = tag.Groups[1].Value, Size = long.Parse(exe.Groups[1].Value), ExeUrl = exe.Groups[2].Value };
        }

        static bool IsNewer(string latest, string current)
        {
            try { return new Version(Pad(latest)) > new Version(Pad(current)); }
            catch { return false; }
        }

        static string Pad(string v) { return v.Split('.').Length < 2 ? v + ".0" : v; }

        static void Ask(Release r)
        {
            shown = new UpdateForm(r.Version);
            shown.No += delegate { NextLook = DateTime.UtcNow + Pause; };
            shown.Yes += delegate { Download(r, shown); };
            shown.Show();
            shown.Activate();
        }

        static void Download(Release r, UpdateForm form)
        {
            string tmp = Path.Combine(Path.GetTempPath(), "Butterfly-" + r.Version + ".exe");
            WebClient wc = Client();
            wc.DownloadProgressChanged += delegate(object s, DownloadProgressChangedEventArgs e)
            {
                int pct = r.Size > 0 ? (int)(e.BytesReceived * 100 / r.Size) : e.ProgressPercentage;
                form.Progress(Math.Min(100, pct));
            };
            wc.DownloadFileCompleted += delegate(object s, System.ComponentModel.AsyncCompletedEventArgs e)
            {
                wc.Dispose();
                if (e.Error != null || e.Cancelled || !LooksRight(tmp, r.Size))
                {
                    try { File.Delete(tmp); } catch { }
                    form.Failed();
                    return;
                }
                Swap(tmp);
            };
            wc.DownloadFileAsync(new Uri(r.ExeUrl), tmp);
        }

        /// <summary>The right size and a Windows program header ("MZ"): not a half-finished or wrong download.</summary>
        static bool LooksRight(string path, long size)
        {
            try
            {
                var fi = new FileInfo(path);
                if (!fi.Exists || fi.Length < 100000 || (size > 0 && fi.Length != size)) return false;
                using (FileStream fs = File.OpenRead(path)) return fs.ReadByte() == 'M' && fs.ReadByte() == 'Z';
            }
            catch { return false; }
        }

        /// <summary>A small script waits until this copy has quit, puts the new exe in its place and starts it.</summary>
        static void Swap(string newExe)
        {
            string target = Application.ExecutablePath;
            string cmd = Path.Combine(Path.GetTempPath(), "butterfly-update.cmd");
            File.WriteAllText(cmd,
                "@echo off\r\n" +
                "set n=0\r\n" +
                ":again\r\n" +
                "ping -n 2 127.0.0.1 >nul\r\n" +
                "copy /y \"" + newExe + "\" \"" + target + "\" >nul 2>&1\r\n" +
                "if not errorlevel 1 goto ok\r\n" +
                "set /a n+=1\r\n" +
                "if %n% lss 30 goto again\r\n" +
                ":ok\r\n" +
                "start \"\" \"" + target + "\" --portable\r\n" +
                "del \"" + newExe + "\" >nul 2>&1\r\n" +
                "del \"%~f0\" >nul 2>&1\r\n");
            Process.Start(new ProcessStartInfo("cmd.exe", "/c \"" + cmd + "\"") { CreateNoWindow = true, UseShellExecute = false, WindowStyle = ProcessWindowStyle.Hidden });
            Application.Exit();
        }
    }

    /// <summary>"A new version is out. Update?" with Yes / No, then a progress line while downloading.</summary>
    sealed class UpdateForm : Form
    {
        public event Action Yes, No;
        readonly Label line = new Label();
        readonly Button yes = new Button(), no = new Button();
        bool answered, failed;

        public UpdateForm(string version)
        {
            Text = L.T("Бабочка — обновление");
            Font = new Font("Segoe UI", 10f);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = MinimizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            TopMost = true;
            AutoScaleMode = AutoScaleMode.Font;
            AutoSize = true;
            AutoSizeMode = AutoSizeMode.GrowAndShrink;
            Padding = new Padding(18, 14, 18, 14);
            try { Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }

            var panel = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, Dock = DockStyle.Fill };
            Controls.Add(panel);
            panel.Controls.Add(new Label
            {
                Text = string.Format(L.T("Вышла новая версия {0}."), version), AutoSize = true, Tag = "header",
                Font = new Font("Segoe UI", 13f, FontStyle.Bold), Margin = new Padding(0, 0, 0, 6)
            });
            line.Text = L.T("Обновиться? Программа перезапустится сама, настройки сохранятся.");
            line.AutoSize = true;
            line.MaximumSize = new Size(420, 0);
            line.Margin = new Padding(0, 0, 0, 14);
            panel.Controls.Add(line);

            var buttons = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.LeftToRight, Margin = new Padding(0), Anchor = AnchorStyles.Right };
            yes.Text = L.T("Да"); no.Text = L.T("Нет");
            foreach (Button b in new[] { yes, no }) { b.AutoSize = true; b.MinimumSize = new Size(96, 32); b.Margin = new Padding(0, 0, 8, 0); }
            buttons.Controls.Add(yes);
            buttons.Controls.Add(no);
            panel.Controls.Add(buttons);
            AcceptButton = yes;

            yes.Click += delegate
            {
                if (failed) { try { Process.Start(Updater.Page); } catch { } Close(); return; }
                answered = true;
                yes.Enabled = no.Enabled = false;
                line.Text = L.T("Загрузка…");
                if (Yes != null) Yes();
            };
            no.Click += delegate { Close(); };
            FormClosed += delegate { if (!answered && No != null) No(); };
            Theme.Apply(this);
        }

        public void Progress(int pct) { line.Text = L.T("Загрузка…") + " " + pct + "%"; }

        public void Failed()
        {
            line.Text = L.T("Не удалось скачать обновление. Можно скачать его вручную со страницы программы.");
            no.Text = L.T("Закрыть");
            no.Enabled = true;
            yes.Text = L.T("Открыть страницу");
            yes.Enabled = true;
            failed = true;
            answered = false;          // closing now counts as "No": ask again in 12 hours
        }
    }
}
