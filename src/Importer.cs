using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;

namespace ButterflyCursor
{
    /// <summary>
    /// Turns ordinary pictures (JPG etc. on a plain background) into transparent PNG sprites
    /// in the "creatures" folder.
    /// </summary>
    static class Importer
    {
        static readonly string[] Convertible = { ".jpg", ".jpeg", ".jfif", ".bmp", ".gif" };
        static readonly HashSet<string> failed = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        /// <summary>Converts every picture in the creatures folder that has no PNG twin yet.</summary>
        public static void ConvertPending()
        {
            try
            {
                if (!Directory.Exists(Creature.Folder)) return;
                foreach (string f in Directory.GetFiles(Creature.Folder))
                {
                    if (Array.IndexOf(Convertible, Path.GetExtension(f).ToLowerInvariant()) < 0) continue;
                    string png = Path.ChangeExtension(f, ".png");
                    if (File.Exists(png) || failed.Contains(f)) continue;
                    try { CutBackground(f, png); }
                    catch { failed.Add(f); }
                }
            }
            catch { }
        }

        /// <summary>Adds a picture chosen by the user; returns the id of the new creature.</summary>
        public static string Import(string source)
        {
            Directory.CreateDirectory(Creature.Folder);
            string name = Path.GetFileNameWithoutExtension(source);
            string dest = Path.Combine(Creature.Folder, name + ".png");
            for (int i = 2; File.Exists(dest); i++) dest = Path.Combine(Creature.Folder, name + " " + i + ".png");

            if (HasTransparency(source)) File.Copy(source, dest);
            else CutBackground(source, dest);
            return "file:" + Path.GetFileName(dest).ToLowerInvariant();
        }

        static Bitmap LoadScaled(string path, int maxSide)
        {
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read))
            using (var src = new Bitmap(fs))
            {
                float k = Math.Min(1f, (float)maxSide / Math.Max(src.Width, src.Height));
                int w = Math.Max(1, (int)(src.Width * k)), h = Math.Max(1, (int)(src.Height * k));
                var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
                using (Graphics g = Graphics.FromImage(bmp))
                {
                    g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                    g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                    g.DrawImage(src, new Rectangle(0, 0, w, h));
                }
                return bmp;
            }
        }

        static byte[] Pixels(Bitmap bmp)
        {
            var data = new byte[bmp.Width * bmp.Height * 4];
            BitmapData bd = bmp.LockBits(new Rectangle(0, 0, bmp.Width, bmp.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            Marshal.Copy(bd.Scan0, data, 0, data.Length);
            bmp.UnlockBits(bd);
            return data;
        }

        static bool HasTransparency(string path)
        {
            try
            {
                using (Bitmap bmp = LoadScaled(path, 200))
                {
                    byte[] px = Pixels(bmp);
                    int clear = 0;
                    for (int i = 3; i < px.Length; i += 4) if (px[i] < 128) clear++;
                    return clear > px.Length / 4 / 50;      // at least 2% see-through
                }
            }
            catch { return false; }
        }

        static int Median(List<byte> values)
        {
            values.Sort();
            return values[values.Count / 2];
        }

        /// <summary>
        /// Background = pixels of the border colour that are connected to the picture's edge.
        /// Everything else is kept, cropped, centred in a square and saved as PNG.
        /// </summary>
        public static void CutBackground(string source, string dest)
        {
            using (Bitmap bmp = LoadScaled(source, 1000))
            {
                int w = bmp.Width, h = bmp.Height, n = w * h;
                byte[] px = Pixels(bmp);

                // page colour = median of the border pixels
                var bs = new List<byte>(); var gs = new List<byte>(); var rs = new List<byte>();
                Action<int> sample = delegate(int i) { bs.Add(px[i * 4]); gs.Add(px[i * 4 + 1]); rs.Add(px[i * 4 + 2]); };
                for (int x = 0; x < w; x++) { sample(x); sample((h - 1) * w + x); }
                for (int y = 0; y < h; y++) { sample(y * w); sample(y * w + w - 1); }
                int bgB = Median(bs), bgG = Median(gs), bgR = Median(rs);
                // a white sticker outline on an off-white page needs a tight tolerance
                int tol = Math.Max(bgB, Math.Max(bgG, bgR)) < 250 ? 7 : 14;

                var similar = new bool[n];
                for (int i = 0; i < n; i++)
                {
                    int d = Math.Max(Math.Abs(px[i * 4] - bgB), Math.Max(Math.Abs(px[i * 4 + 1] - bgG), Math.Abs(px[i * 4 + 2] - bgR)));
                    similar[i] = d <= tol;
                }

                // flood fill from the edges
                var outside = new bool[n];
                var stack = new int[n];
                int top = 0;
                Action<int> seed = delegate(int i) { if (similar[i] && !outside[i]) { outside[i] = true; stack[top++] = i; } };
                for (int x = 0; x < w; x++) { seed(x); seed((h - 1) * w + x); }
                for (int y = 0; y < h; y++) { seed(y * w); seed(y * w + w - 1); }
                while (top > 0)
                {
                    int i = stack[--top], x = i % w, y = i / w;
                    if (x > 0) seed(i - 1);
                    if (x < w - 1) seed(i + 1);
                    if (y > 0) seed(i - w);
                    if (y < h - 1) seed(i + w);
                }

                // remove one-pixel crumbs (erode + dilate)
                var eroded = new bool[n];
                for (int y = 1; y < h - 1; y++)
                    for (int x = 1; x < w - 1; x++)
                    {
                        int i = y * w + x;
                        eroded[i] = !outside[i] && !outside[i - 1] && !outside[i + 1] && !outside[i - w] && !outside[i + w]
                                    && !outside[i - w - 1] && !outside[i - w + 1] && !outside[i + w - 1] && !outside[i + w + 1];
                    }
                var inside = new bool[n];
                for (int y = 1; y < h - 1; y++)
                    for (int x = 1; x < w - 1; x++)
                    {
                        int i = y * w + x;
                        inside[i] = eroded[i] || eroded[i - 1] || eroded[i + 1] || eroded[i - w] || eroded[i + w]
                                    || eroded[i - w - 1] || eroded[i - w + 1] || eroded[i + w - 1] || eroded[i + w + 1];
                    }

                // keep the real parts, drop specks smaller than 1% of the biggest one
                var label = new int[n];
                var sizes = new List<int> { 0 };
                for (int start = 0; start < n; start++)
                {
                    if (!inside[start] || label[start] != 0) continue;
                    int id = sizes.Count, count = 0;
                    top = 0; stack[top++] = start; label[start] = id;
                    while (top > 0)
                    {
                        int i = stack[--top], x = i % w, y = i / w;
                        count++;
                        if (x > 0 && inside[i - 1] && label[i - 1] == 0) { label[i - 1] = id; stack[top++] = i - 1; }
                        if (x < w - 1 && inside[i + 1] && label[i + 1] == 0) { label[i + 1] = id; stack[top++] = i + 1; }
                        if (y > 0 && inside[i - w] && label[i - w] == 0) { label[i - w] = id; stack[top++] = i - w; }
                        if (y < h - 1 && inside[i + w] && label[i + w] == 0) { label[i + w] = id; stack[top++] = i + w; }
                    }
                    sizes.Add(count);
                }
                int biggest = 0;
                foreach (int s in sizes) biggest = Math.Max(biggest, s);
                // nothing left, or nothing removed: there is no plain background to cut
                if (biggest == 0) throw new InvalidOperationException("empty");

                int x0 = w, y0 = h, x1 = -1, y1 = -1;
                for (int i = 0; i < n; i++)
                {
                    inside[i] = inside[i] && sizes[label[i]] * 100 >= biggest;
                    if (!inside[i]) continue;
                    int x = i % w, y = i / w;
                    if (x < x0) x0 = x; if (x > x1) x1 = x;
                    if (y < y0) y0 = y; if (y > y1) y1 = y;
                }

                // soft edge: small blur of the mask becomes the alpha channel
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                    {
                        int sum = 0;
                        for (int dy = -1; dy <= 1; dy++)
                            for (int dx = -1; dx <= 1; dx++)
                            {
                                int xx = x + dx, yy = y + dy;
                                if (xx < 0 || yy < 0 || xx >= w || yy >= h || !inside[yy * w + xx]) continue;
                                sum += (dx == 0 ? 2 : 1) * (dy == 0 ? 2 : 1);
                            }
                        px[(y * w + x) * 4 + 3] = (byte)(sum * 255 / 16);
                    }

                using (var cut = new Bitmap(w, h, PixelFormat.Format32bppArgb))
                {
                    BitmapData bd = cut.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
                    Marshal.Copy(px, 0, bd.Scan0, px.Length);
                    cut.UnlockBits(bd);

                    int cw = x1 - x0 + 1, ch = y1 - y0 + 1;
                    int side = Math.Max(cw, ch) + 8;
                    float k = Math.Min(1f, 400f / side);
                    int outSide = Math.Max(16, (int)(side * k));
                    using (var result = new Bitmap(outSide, outSide, PixelFormat.Format32bppArgb))
                    {
                        using (Graphics g = Graphics.FromImage(result))
                        {
                            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
                            g.PixelOffsetMode = PixelOffsetMode.HighQuality;
                            g.DrawImage(cut,
                                new RectangleF((side - cw) / 2f * k, (side - ch) / 2f * k, cw * k, ch * k),
                                new RectangleF(x0, y0, cw, ch), GraphicsUnit.Pixel);
                        }
                        result.Save(dest, ImageFormat.Png);
                    }
                }
            }
        }
    }
}
