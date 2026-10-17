using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

namespace ButterflyCursor
{
    // ---------- how loud the computer is playing right now (Windows Core Audio peak meter) ----------

    [ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
    class MMDeviceEnumeratorCom { }

    [ComImport, Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDeviceEnumerator
    {
        [PreserveSig] int EnumAudioEndpoints(int dataFlow, int stateMask, out IntPtr devices);
        [PreserveSig] int GetDefaultAudioEndpoint(int dataFlow, int role, out IMMDevice endpoint);
    }

    [ComImport, Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IMMDevice
    {
        [PreserveSig] int Activate(ref Guid iid, int clsCtx, IntPtr activationParams, [MarshalAs(UnmanagedType.IUnknown)] out object iface);
    }

    [ComImport, Guid("C02216F6-8C67-4B5B-9D00-D008E73E0064"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface IAudioMeterInformation
    {
        [PreserveSig] int GetPeakValue(out float peak);
    }

    /// <summary>Peak level (0..1) of everything the speakers play. Only a level meter: nothing is recorded.</summary>
    sealed class AudioMeter
    {
        IAudioMeterInformation meter;
        double nextConnect;

        public float Peak(double now)
        {
            // reconnect from time to time, so a new default device (headphones…) is picked up
            if (now >= nextConnect)
            {
                nextConnect = now + 10;
                meter = null;
                try
                {
                    var en = (IMMDeviceEnumerator)new MMDeviceEnumeratorCom();
                    IMMDevice dev;
                    if (en.GetDefaultAudioEndpoint(0 /* render */, 1 /* multimedia */, out dev) == 0 && dev != null)
                    {
                        Guid iid = typeof(IAudioMeterInformation).GUID;
                        object o;
                        if (dev.Activate(ref iid, 23 /* CLSCTX_ALL */, IntPtr.Zero, out o) == 0)
                            meter = o as IAudioMeterInformation;
                    }
                }
                catch { meter = null; }
            }
            if (meter == null) return 0f;
            try
            {
                float p;
                return meter.GetPeakValue(out p) == 0 ? Math.Max(0f, Math.Min(1f, p)) : 0f;
            }
            catch { meter = null; return 0f; }
        }
    }

    // ---------- seasons and holidays ----------

    enum SeasonFx { None = 0, Snow = 1, Confetti = 2, Petals = 3, Leaves = 4, Pumpkins = 5, Rain = 6, Twinkle = 7 }

    static class Season
    {
        public static DateTime Today
        {
            get
            {
                string fake = Environment.GetEnvironmentVariable("BUTTERFLY_TEST_DATE");
                DateTime d;
                if (!string.IsNullOrEmpty(fake) && DateTime.TryParse(fake, out d)) return d;
                return DateTime.Now;
            }
        }

        /// <summary>What falls along with the fairy dust on a given day.</summary>
        public static SeasonFx[] Current()
        {
            DateTime d = Today;
            int m = d.Month, day = d.Day;
            if ((m == 12 && day >= 25) || (m == 1 && day <= 7)) return new[] { SeasonFx.Confetti, SeasonFx.Snow };   // New Year
            if ((m == 10 && day >= 20) || (m == 11 && day <= 2)) return new[] { SeasonFx.Pumpkins, SeasonFx.Leaves }; // Halloween
            if (m == 12 || m == 1 || m == 2) return new[] { SeasonFx.Snow };
            if (m >= 3 && m <= 5) return new[] { SeasonFx.Petals };
            if (m >= 9 && m <= 11) return new[] { SeasonFx.Leaves };
            return new SeasonFx[0];                                                                    // summer: fireflies only
        }

        public static bool Night
        {
            get { int h = Today.Hour; return h >= 20 || h < 6; }
        }
    }

    /// <summary>Little pictures for the seasonal particles, drawn once and cached (4 transparency steps).</summary>
    static class SeasonSprites
    {
        public const int Variants = 4, Levels = 4;
        static readonly Dictionary<int, Bitmap> cache = new Dictionary<int, Bitmap>();

        public static Bitmap Get(SeasonFx kind, int variant, float alpha)
        {
            int level = Math.Max(1, Math.Min(Levels, (int)Math.Ceiling(alpha * Levels)));
            int key = ((int)kind * 16 + variant % Variants) * 16 + level;
            Bitmap b;
            if (cache.TryGetValue(key, out b)) return b;

            using (Bitmap full = Draw(kind, variant % Variants))
            {
                b = new Bitmap(full.Width, full.Height, PixelFormat.Format32bppPArgb);
                using (Graphics g = Graphics.FromImage(b))
                using (var attr = new ImageAttributes())
                {
                    var cm = new ColorMatrix { Matrix33 = (float)level / Levels };
                    attr.SetColorMatrix(cm);
                    g.DrawImage(full, new Rectangle(0, 0, full.Width, full.Height), 0, 0, full.Width, full.Height, GraphicsUnit.Pixel, attr);
                }
            }
            cache[key] = b;
            return b;
        }

        static Bitmap Draw(SeasonFx kind, int v)
        {
            const int S = 40;
            var b = new Bitmap(S, S, PixelFormat.Format32bppArgb);
            using (Graphics g = Graphics.FromImage(b))
            {
                g.SmoothingMode = SmoothingMode.AntiAlias;
                g.TranslateTransform(S / 2f, S / 2f);
                switch (kind)
                {
                    case SeasonFx.Snow:
                        using (var glow = new SolidBrush(Color.FromArgb(60, 180, 220, 255))) g.FillEllipse(glow, -15, -15, 30, 30);
                        using (var pen = new Pen(Color.White, 2.4f) { StartCap = LineCap.Round, EndCap = LineCap.Round })
                            for (int i = 0; i < 6; i++)
                            {
                                g.DrawLine(pen, 0, 0, 0, -14);
                                g.DrawLine(pen, 0, -8, -4, -12);
                                g.DrawLine(pen, 0, -8, 4, -12);
                                g.RotateTransform(60);
                            }
                        break;

                    case SeasonFx.Confetti:
                        Color[] cc = { Color.FromArgb(255, 80, 90), Color.FromArgb(255, 210, 60), Color.FromArgb(80, 210, 120), Color.FromArgb(90, 160, 255) };
                        using (var br = new SolidBrush(cc[v])) g.FillRectangle(br, -9, -5, 18, 10);
                        using (var hl = new SolidBrush(Color.FromArgb(90, 255, 255, 255))) g.FillRectangle(hl, -9, -5, 18, 3);
                        break;

                    case SeasonFx.Petals:
                        Color[] pc = { Color.FromArgb(255, 190, 215), Color.FromArgb(255, 170, 200), Color.FromArgb(255, 215, 230), Color.FromArgb(250, 160, 190) };
                        using (var path = new GraphicsPath())
                        {
                            path.AddBezier(0, 15, -14, 4, -9, -12, -2, -14);
                            path.AddLine(-2, -14, 0, -10);
                            path.AddLine(0, -10, 2, -14);
                            path.AddBezier(2, -14, 9, -12, 14, 4, 0, 15);
                            using (var br = new LinearGradientBrush(new PointF(0, 15), new PointF(0, -14), Color.White, pc[v])) g.FillPath(br, path);
                            using (var pen = new Pen(Color.FromArgb(120, 230, 120, 160), 1f)) g.DrawPath(pen, path);
                        }
                        break;

                    case SeasonFx.Leaves:
                        Color[] lc = { Color.FromArgb(240, 120, 30), Color.FromArgb(215, 50, 35), Color.FromArgb(245, 190, 40), Color.FromArgb(170, 95, 40) };
                        using (var path = new GraphicsPath())
                        {
                            path.AddBezier(0, -16, 12, -10, 14, 6, 0, 14);
                            path.AddBezier(0, 14, -14, 6, -12, -10, 0, -16);
                            using (var br = new SolidBrush(lc[v])) g.FillPath(br, path);
                            using (var pen = new Pen(Color.FromArgb(150, 90, 40, 10), 1.4f))
                            {
                                g.DrawLine(pen, 0, -14, 0, 18);
                                g.DrawLine(pen, 0, -4, 6, -9);
                                g.DrawLine(pen, 0, -4, -6, -9);
                                g.DrawLine(pen, 0, 4, 7, -1);
                                g.DrawLine(pen, 0, 4, -7, -1);
                            }
                        }
                        break;

                    case SeasonFx.Pumpkins:
                        using (var glow = new SolidBrush(Color.FromArgb(70, 255, 160, 40))) g.FillEllipse(glow, -18, -16, 36, 34);
                        using (var br = new SolidBrush(Color.FromArgb(245, 135, 25)))
                        {
                            g.FillEllipse(br, -14, -9, 16, 20);
                            g.FillEllipse(br, -2, -9, 16, 20);
                        }
                        using (var br = new SolidBrush(Color.FromArgb(255, 160, 45))) g.FillEllipse(br, -8, -10, 16, 22);
                        using (var stem = new Pen(Color.FromArgb(70, 130, 40), 3f)) g.DrawLine(stem, 0, -10, 2, -15);
                        using (var face = new SolidBrush(Color.FromArgb(70, 30, 0)))
                        {
                            g.FillPolygon(face, new[] { new PointF(-7, -3), new PointF(-3, -3), new PointF(-5, -7) });
                            g.FillPolygon(face, new[] { new PointF(3, -3), new PointF(7, -3), new PointF(5, -7) });
                            g.FillPie(face, -6, 0, 12, 7, 0, 180);
                        }
                        break;
                }
            }
            return b;
        }
    }

    /// <summary>A shuriken the ninja throws at the spot that was clicked.</summary>
    sealed class Shot
    {
        public float X, Y, Vx, Vy, Rot, Life;
    }
}
