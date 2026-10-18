using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace ButterflyCursor
{
    sealed class SettingsForm : Form
    {
        readonly TableLayoutPanel grid = new TableLayoutPanel();
        readonly List<Action> refreshers = new List<Action>();
        readonly ComboBox styleBox = new ComboBox(), themeBox = new ComboBox();
        CreaturePicker picker;
        List<Creature> creatures;
        bool loading;

        public SettingsForm(Icon icon)
        {
            Text = L.T("Бабочка — настройки");
            Icon = icon;
            Font = new Font("Segoe UI", 9f);
            FormBorderStyle = FormBorderStyle.FixedDialog;
            MaximizeBox = false;
            MinimizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            AutoScaleMode = AutoScaleMode.Font;
            // the list is long: it scrolls when the window would not fit on the screen
            scroller.Dock = DockStyle.Fill;
            scroller.AutoScroll = true;
            Controls.Add(scroller);

            grid.Location = new Point(14, 8);
            grid.Margin = new Padding(0, 0, 0, 12);
            grid.ColumnCount = 3;
            grid.AutoSize = true;
            grid.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 250));
            grid.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute, 64));
            scroller.Controls.Add(grid);

            // ----- creature: title with the light/dark switch, then the picker -----
            float scale;
            using (Graphics sg = CreateGraphics()) scale = sg.DpiX / 96f;
            var head = new TableLayoutPanel { ColumnCount = 2, RowCount = 1, AutoSize = true, Dock = DockStyle.Fill, Margin = new Padding(0, 6, 0, 6) };
            head.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 100));
            head.ColumnStyles.Add(new ColumnStyle(SizeType.AutoSize));
            head.Controls.Add(new Label { Text = L.T("Существо"), AutoSize = true, Font = new Font("Segoe UI", 13f, FontStyle.Bold), Anchor = AnchorStyles.Left, Margin = new Padding(0) }, 0, 0);
            var themeSwitch = new ThemeToggle { Size = new Size((int)(56 * scale), (int)(28 * scale)), Anchor = AnchorStyles.Right, Margin = new Padding(0, 2, 2, 0) };
            tips.SetToolTip(themeSwitch, L.T("Светлая / тёмная тема"));
            themeSwitch.Toggled += delegate { Cfg.DarkTheme = !Cfg.DarkTheme; Cfg.Apply(); };
            head.Controls.Add(themeSwitch, 1, 0);
            Wide(head);

            picker = new CreaturePicker(scale) { Margin = new Padding(0, 0, 0, 8) };
            picker.Picked += delegate(Creature c)
            {
                if (loading || c == null) return;
                Cfg.CreatureId = c.Id;
                loading = true;
                styleBox.SelectedIndex = (int)Cfg.StyleOf(c);
                loading = false;
                UpdateFlagRow();
                Cfg.Apply();
            };
            Wide(picker);
            styleBox.DropDownStyle = themeBox.DropDownStyle = ComboBoxStyle.DropDownList;
            styleBox.Items.AddRange(new object[] { L.T("Летает (машет крыльями)"), L.T("Ползает (вид сверху)"), L.T("Скользит, как улитка (вид сбоку)"), L.T("Парит (не поворачивается)"), L.T("Бежит (вид сбоку, по кадрам)"), L.T("Развевается, как флаг") });
            Row(L.T("Как двигается"), styleBox);
            flagBox.DropDownStyle = ComboBoxStyle.DropDownList;
            flagBox.MaxDropDownItems = 20;
            for (int i = 0; i < Flags.Codes.Count; i++) flagBox.Items.Add(Flags.Names[i] + " (" + Flags.Codes[i].ToUpperInvariant() + ")");
            // the country list only matters for the flag, so it is shown only then
            int flagRow = NewRow();
            flagLabel = new Label { Text = L.T("Флаг страны"), AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(3, 6, 12, 6) };
            flagBox.Dock = DockStyle.Fill;
            grid.Controls.Add(flagLabel, 0, flagRow);
            grid.Controls.Add(flagBox, 1, flagRow);
            flagBox.SelectedIndexChanged += delegate
            {
                if (loading || flagBox.SelectedIndex < 0) return;
                // picking a country also switches the creature to the flag
                Cfg.FlagCode = Flags.Codes[flagBox.SelectedIndex];
                Cfg.CreatureId = "flag";
                Cfg.Apply();
                Reload();
            };
            refreshers.Add(delegate { flagBox.SelectedIndex = Math.Max(0, Flags.Codes.IndexOf(Cfg.FlagCode)); });
            styleBox.SelectedIndexChanged += delegate
            {
                if (loading || picker.Selected == null) return;
                Cfg.SetStyle(picker.Selected, (MoveStyle)styleBox.SelectedIndex);
                Cfg.Apply();
            };
            Slider(L.T("Размер"), 32, 200, delegate { return Cfg.Size; }, delegate(int v) { Cfg.Size = v; }, "{0} px");
            var add = new Button { Text = L.T("Добавить картинку…"), AutoSize = true, FlatStyle = FlatStyle.System, Margin = new Padding(3, 2, 10, 2) };
            tips.SetToolTip(add, L.T("Свои картинки появятся в разделе «Мои картинки»"));
            add.Click += delegate { AddPictures(); };
            var link = new LinkLabel { Text = L.T("Открыть папку с картинками"), AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(3, 8, 3, 6) };
            link.LinkClicked += delegate
            {
                try { Directory.CreateDirectory(Creature.Folder); Process.Start(Creature.Folder); } catch { }
            };
            var own = new FlowLayoutPanel { AutoSize = true, Margin = new Padding(0, 2, 0, 2) };
            own.Controls.Add(add);
            own.Controls.Add(link);
            Wide(own);

            // ----- behaviour -----
            Header(L.T("Поведение"));
            Slider(L.T("Скорость"), 1, 10, delegate { return Cfg.Speed; }, delegate(int v) { Cfg.Speed = v; }, "{0}");
            var home = Check(L.T("Возвращаться к кнопке «Пуск», когда мышь не двигается"),
                delegate { return Cfg.GoHome; }, delegate(bool v) { Cfg.GoHome = v; });
            var idle = new NumericUpDown { Minimum = 1, Maximum = 3600, Width = 70, Anchor = AnchorStyles.Left };
            Row(L.T("Через сколько секунд покоя"), idle);
            idle.ValueChanged += delegate { if (!loading) { Cfg.IdleSec = (int)idle.Value; Cfg.Apply(); } };
            refreshers.Add(delegate { idle.Value = Cfg.IdleSec; idle.Enabled = Cfg.GoHome; });
            home.CheckedChanged += delegate { idle.Enabled = home.Checked; };

            Check(L.T("Прятаться, когда игра или видео открыты на весь экран"),
                delegate { return Cfg.HideFullscreen; }, delegate(bool v) { Cfg.HideFullscreen = v; });

            var apps = new Button { Text = L.T("Программы, в которых прятаться…"), AutoSize = true, FlatStyle = FlatStyle.System, Margin = new Padding(3, 4, 3, 2) };
            apps.Click += delegate { using (var dlg = new AppsForm(Icon)) dlg.ShowDialog(this); };
            Wide(apps);

            // ----- dust -----
            Header(L.T("Пыльца и свечение"));
            Check(L.T("Оставлять за собой светящуюся пыльцу"), delegate { return Cfg.Dust; }, delegate(bool v) { Cfg.Dust = v; });
            grid.ColumnStyles[2].SizeType = SizeType.AutoSize;

            // the user's own palette: click a swatch to change it, right-click to remove, "+" to add
            swatches.AutoSize = true;
            swatches.MaximumSize = new Size(330, 0);
            swatches.Margin = new Padding(0, 2, 0, 2);
            int paletteRow = NewRow();
            grid.Controls.Add(new Label { Text = L.T("Цвета пылинок"), AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(3, 6, 12, 6) }, 0, paletteRow);
            grid.Controls.Add(swatches, 1, paletteRow);
            grid.SetColumnSpan(swatches, 2);
            refreshers.Add(RebuildSwatches);

            foreach (string name in Cfg.PresetNames) themeBox.Items.Add(L.T(name));
            Row(L.T("Готовый набор"), themeBox);
            themeBox.SelectedIndexChanged += delegate
            {
                if (loading) return;
                int i = themeBox.SelectedIndex;
                if (i == Cfg.CustomPreset) return;
                Cfg.Rainbow = i == Cfg.RainbowPreset;
                if (!Cfg.Rainbow) Cfg.Colors = Cfg.Preset(i);
                Cfg.Apply();
                RebuildSwatches();
            };
            refreshers.Add(delegate { themeBox.SelectedIndex = Cfg.PresetIndex(); });
            Slider(L.T("Количество пылинок"), 0, 100, delegate { return Cfg.DustAmount; }, delegate(int v) { Cfg.DustAmount = v; }, "{0}%");
            Slider(L.T("Размер пылинок"), 0, 100, delegate { return Cfg.DustSize; }, delegate(int v) { Cfg.DustSize = v; }, "{0}%");
            Slider(L.T("Как долго светятся"), 0, 100, delegate { return Cfg.DustLife; }, delegate(int v) { Cfg.DustLife = v; }, "{0}%");
            Slider(L.T("Яркость"), 10, 100, delegate { return Cfg.DustBright; }, delegate(int v) { Cfg.DustBright = v; }, "{0}%");
            Slider(L.T("Сияние вокруг существа"), 0, 100, delegate { return Cfg.Aura; }, delegate(int v) { Cfg.Aura = v; }, "{0}%");
            var auraColor = Swatch(0);
            auraColor.Anchor = AnchorStyles.Left;
            auraColor.Click += delegate
            {
                int rgb;
                if (!PickColor(Cfg.AuraRgb, out rgb)) return;
                Cfg.AuraRgb = rgb;
                auraColor.BackColor = Color.FromArgb(255, Color.FromArgb(rgb));
                Cfg.Apply();
            };
            Row(L.T("Цвет сияния"), auraColor);
            refreshers.Add(delegate { auraColor.BackColor = Color.FromArgb(255, Color.FromArgb(Cfg.AuraRgb)); });

            // ----- fun -----
            Header(L.T("Развлечения"));
            Check(L.T("Реакция на клик: искры, кувырок, ниндзя бросает сюрикен"), delegate { return Cfg.ClickFx; }, delegate(bool v) { Cfg.ClickFx = v; });
            Check(L.T("Сезонные эффекты: снег, листья, сакура, праздники"), delegate { return Cfg.Seasons; }, delegate(bool v) { Cfg.Seasons = v; });
            Check(L.T("Танцевать под музыку"), delegate { return Cfg.Music; }, delegate(bool v) { Cfg.Music = v; });
            Check(L.T("Ночное свечение: вечером и ночью светится ярче"), delegate { return Cfg.NightGlow; }, delegate(bool v) { Cfg.NightGlow = v; });
            var demo = new Button { AutoSize = true, FlatStyle = FlatStyle.System, Margin = new Padding(3, 6, 3, 2) };
            Action demoText = delegate
            {
                demo.Text = Overlay.Current != null && Overlay.Current.Demo ? L.T("■ Остановить демонстрацию") : L.T("▶ Демонстрация для видео");
            };
            demo.Click += delegate { if (Overlay.Current != null) Overlay.Current.ToggleDemo(); };
            if (Overlay.Current != null) Overlay.Current.DemoChanged += delegate { if (!demo.IsDisposed) demoText(); };
            refreshers.Add(demoText);
            Wide(demo);

            // ----- misc -----
            Header(L.T("Прочее"));
            var langBox = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList };
            langBox.Items.Add(L.T(L.Names[0]));
            for (int i = 1; i < L.Names.Length; i++) langBox.Items.Add(L.Names[i]);
            Row(L.T("Язык"), langBox);
            refreshers.Add(delegate { langBox.SelectedIndex = Math.Max(0, Array.IndexOf(L.Codes, Cfg.Lang)); });
            langBox.SelectedIndexChanged += delegate
            {
                if (loading) return;
                Cfg.Lang = L.Codes[langBox.SelectedIndex];
                Cfg.Apply();
            };
            var auto = new CheckBox { Text = L.T("Запускать вместе с Windows"), AutoSize = true, Margin = new Padding(3, 4, 3, 4) };
            Wide(auto);
            refreshers.Add(delegate { auto.Checked = Cfg.Autostart; });
            auto.CheckedChanged += delegate { if (!loading) Cfg.Autostart = auto.Checked; };
            var desk = new CheckBox { Text = L.T("Пункт «Бабочка — настройки» в меню рабочего стола (правый клик)"), AutoSize = true, Margin = new Padding(3, 4, 3, 4) };
            Wide(desk);
            refreshers.Add(delegate { desk.Checked = Cfg.DesktopMenu; });
            desk.CheckedChanged += delegate { if (!loading) Cfg.DesktopMenu = desk.Checked; };
            Check(L.T("Сообщать о новых версиях"), delegate { return Cfg.CheckUpdates; }, delegate(bool v) { Cfg.CheckUpdates = v; });

            // the buttons stay pinned at the bottom of the window, outside the scrolling list
            buttons.FlowDirection = FlowDirection.RightToLeft;
            buttons.Dock = DockStyle.Bottom;
            buttons.AutoSize = true;
            buttons.AutoSizeMode = AutoSizeMode.GrowAndShrink;
            buttons.Padding = new Padding(10, 8, 22, 10);
            buttons.Tag = "bar";
            var close = new Button { Text = L.T("Закрыть"), AutoSize = true, FlatStyle = FlatStyle.System, MinimumSize = new Size(90, 0) };
            var reset = new Button { Text = L.T("По умолчанию"), AutoSize = true, FlatStyle = FlatStyle.System, MinimumSize = new Size(110, 0) };
            close.Click += delegate { Close(); };
            reset.Click += delegate { Cfg.Defaults(); Cfg.Apply(); Reload(); };
            buttons.Controls.Add(close);
            buttons.Controls.Add(reset);
            var help = new Button { Text = L.T("Инструкция"), AutoSize = true, FlatStyle = FlatStyle.System, MinimumSize = new Size(110, 0) };
            help.Click += delegate
            {
                if (helpForm == null || helpForm.IsDisposed) helpForm = new HelpForm(Icon);
                helpForm.Show();
                helpForm.Activate();
            };
            buttons.Controls.Add(help);
            Controls.Add(buttons);
            scroller.BringToFront();             // the list fills whatever space the button bar leaves
            AcceptButton = close;
            CancelButton = close;

            Reload();
            Theme.Apply(this);
        }

        HelpForm helpForm;
        readonly ComboBox flagBox = new ComboBox();
        Label flagLabel;

        readonly Panel scroller = new Panel();
        readonly FlowLayoutPanel buttons = new FlowLayoutPanel();

        void UpdateFlagRow()
        {
            bool on = picker.Selected != null && picker.Selected.Id == "flag";
            flagLabel.Visible = flagBox.Visible = on;
            FitToScreen();
        }

        void FitToScreen()
        {
            Size pref = grid.GetPreferredSize(Size.Empty);
            int bar = buttons.GetPreferredSize(Size.Empty).Height;
            int maxH = Screen.FromPoint(Cursor.Position).WorkingArea.Height - 60;
            int h = Math.Min(pref.Height + 20 + bar, maxH);
            int w = pref.Width + 48 + (pref.Height + 20 + bar > maxH ? SystemInformation.VerticalScrollBarWidth : 0);
            ClientSize = new Size(w, h);
        }
        readonly FlowLayoutPanel swatches = new FlowLayoutPanel();
        readonly ToolTip tips = new ToolTip();
        static readonly int[] customColors = new int[16];

        static Button Swatch(int rgb)
        {
            var b = new Button
            {
                Size = new Size(30, 24), FlatStyle = FlatStyle.Flat, Margin = new Padding(3, 3, 3, 3),
                BackColor = Color.FromArgb(255, Color.FromArgb(rgb)), Cursor = Cursors.Hand, UseVisualStyleBackColor = false, Tag = "swatch"
            };
            b.FlatAppearance.BorderColor = Color.FromArgb(150, 150, 150);
            return b;
        }

        /// <summary>The standard Windows colour picker, opened with the full RGB / spectrum part.</summary>
        bool PickColor(int current, out int rgb)
        {
            using (var dlg = new ColorDialog { FullOpen = true, AnyColor = true, Color = Color.FromArgb(255, Color.FromArgb(current)), CustomColors = customColors })
            {
                bool ok = dlg.ShowDialog(this) == DialogResult.OK;
                Array.Copy(dlg.CustomColors, customColors, Math.Min(16, dlg.CustomColors.Length));
                rgb = dlg.Color.ToArgb() & 0xFFFFFF;
                return ok;
            }
        }

        void PaletteChanged()
        {
            Cfg.Rainbow = false;
            Cfg.Apply();
            RebuildSwatches();
            loading = true;
            themeBox.SelectedIndex = Cfg.PresetIndex();
            loading = false;
        }

        void RebuildSwatches()
        {
            swatches.SuspendLayout();
            foreach (Control old in swatches.Controls) old.Dispose();
            swatches.Controls.Clear();

            for (int i = 0; i < Cfg.Colors.Count && !Cfg.Rainbow; i++)
            {
                int index = i;
                Button b = Swatch(Cfg.Colors[i]);
                tips.SetToolTip(b, L.T("Клик — изменить цвет, правый клик — удалить"));
                b.Click += delegate
                {
                    int rgb;
                    if (!PickColor(Cfg.Colors[index], out rgb)) return;
                    Cfg.Colors[index] = rgb;
                    PaletteChanged();
                };
                b.MouseUp += delegate(object s, MouseEventArgs e)
                {
                    if (e.Button != MouseButtons.Right || Cfg.Colors.Count <= 1) return;
                    Cfg.Colors.RemoveAt(index);
                    PaletteChanged();
                };
                swatches.Controls.Add(b);
            }

            var add = new Button { Text = L.T("+ Добавить цвет"), AutoSize = true, FlatStyle = FlatStyle.System, Margin = new Padding(3, 2, 3, 2) };
            add.Enabled = Cfg.Rainbow || Cfg.Colors.Count < Cfg.MaxColors;
            add.FlatStyle = FlatStyle.Flat; add.BackColor = Theme.Card; add.ForeColor = Theme.Text; add.FlatAppearance.BorderColor = Theme.Border;
            add.Click += delegate
            {
                int rgb;
                if (!PickColor(0x78DCFF, out rgb)) return;
                // leaving the rainbow starts a fresh palette with just the picked colour
                if (Cfg.Rainbow) Cfg.Colors = new List<int>();
                Cfg.Colors.Add(rgb);
                PaletteChanged();
            };
            swatches.Controls.Add(add);
            swatches.ResumeLayout();
        }

        protected override void OnLoad(EventArgs e)
        {
            base.OnLoad(e);
            CenterToScreen();          // the size is only known after the list was filled
        }

        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            if (helpForm != null && !helpForm.IsDisposed) helpForm.Close();
            base.OnFormClosed(e);
        }

        /// <summary>Lets the user pick pictures; their background is removed and they join the list.</summary>
        void AddPictures()
        {
            using (var dlg = new OpenFileDialog())
            {
                dlg.Title = L.T("Добавить картинку…");
                dlg.Filter = L.T("Картинки") + "|*.png;*.jpg;*.jpeg;*.jfif;*.bmp;*.gif";
                dlg.Multiselect = true;
                if (dlg.ShowDialog(this) != DialogResult.OK) return;

                string added = null, problems = "";
                Cursor = Cursors.WaitCursor;
                foreach (string file in dlg.FileNames)
                {
                    try { added = Importer.Import(file); }
                    catch { problems += "\n" + Path.GetFileName(file); }
                }
                Cursor = Cursors.Default;

                if (added != null)
                {
                    Cfg.CreatureId = added;
                    Cfg.Apply();
                    Reload();
                }
                if (problems != "")
                    MessageBox.Show(this, L.T("Не получилось обработать картинку:") + problems, Text,
                        MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        void Reload()
        {
            loading = true;
            creatures = Creature.All();
            int sel = Math.Max(0, creatures.FindIndex(delegate(Creature c) { return c.Id == Cfg.CreatureId; }));
            picker.SetItems(creatures, creatures[sel].Id);
            styleBox.SelectedIndex = (int)Cfg.StyleOf(creatures[sel]);
            UpdateFlagRow();
            foreach (Action a in refreshers) a();
            loading = false;
        }

        protected override void OnActivated(EventArgs e)
        {
            base.OnActivated(e);
            // pick up PNG files dropped into the creatures folder while the window was open
            if (creatures != null && Creature.All().Count != creatures.Count) Reload();
        }

        // ----- layout helpers -----

        int NewRow()
        {
            grid.RowCount++;
            grid.RowStyles.Add(new RowStyle(SizeType.AutoSize));
            return grid.RowCount - 1;
        }

        void Header(string text)
        {
            var l = new Label
            {
                Text = text, AutoSize = true, Font = new Font(Font, FontStyle.Bold),
                Tag = "header", Margin = new Padding(0, 12, 0, 4)
            };
            Wide(l);
        }

        void Wide(Control c)
        {
            int r = NewRow();
            grid.Controls.Add(c, 0, r);
            grid.SetColumnSpan(c, 3);
        }

        void Row(string label, Control c)
        {
            int r = NewRow();
            grid.Controls.Add(new Label { Text = label, AutoSize = true, Anchor = AnchorStyles.Left, Margin = new Padding(3, 6, 12, 6) }, 0, r);
            if (c is ComboBox) c.Dock = DockStyle.Fill;
            grid.Controls.Add(c, 1, r);
        }

        void Slider(string label, int min, int max, Func<int> get, Action<int> set, string format)
        {
            var bar = new TrackBar
            {
                Minimum = min, Maximum = max, TickStyle = TickStyle.None, AutoSize = false, Height = 26,
                Dock = DockStyle.Fill,
                SmallChange = 1, LargeChange = Math.Max(1, (max - min) / 10)
            };
            var value = new Label { AutoSize = true, Anchor = AnchorStyles.Left, Tag = "sub" };
            Row(label, bar);
            grid.Controls.Add(value, 2, grid.RowCount - 1);
            bar.ValueChanged += delegate
            {
                value.Text = string.Format(format, bar.Value);
                if (loading) return;
                set(bar.Value);
                Cfg.Apply();
            };
            refreshers.Add(delegate
            {
                bar.Value = Math.Max(min, Math.Min(max, get()));
                value.Text = string.Format(format, bar.Value);
            });
        }

        CheckBox Check(string label, Func<bool> get, Action<bool> set)
        {
            var box = new CheckBox { Text = label, AutoSize = true, Margin = new Padding(3, 4, 3, 4) };
            Wide(box);
            box.CheckedChanged += delegate { if (!loading) { set(box.Checked); Cfg.Apply(); } };
            refreshers.Add(delegate { box.Checked = get(); });
            return box;
        }
    }
}
