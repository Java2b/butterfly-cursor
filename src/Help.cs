using System.Drawing;
using System.Windows.Forms;

namespace ButterflyCursor
{
    /// <summary>The built-in instructions, shown in the language chosen in the settings.</summary>
    sealed class HelpForm : Form
    {
        public HelpForm(Icon icon)
        {
            Text = L.T("Бабочка — инструкция");
            Icon = icon;
            Font = new Font("Segoe UI", 10f);
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(600, 640);
            MinimizeBox = false;
            Padding = new Padding(16, 12, 4, 12);

            var box = new RichTextBox
            {
                Dock = DockStyle.Fill, ReadOnly = true, BorderStyle = BorderStyle.None,
                ScrollBars = RichTextBoxScrollBars.Vertical, DetectUrls = false, TabStop = false
            };
            Controls.Add(box);

            var heading = new Font("Segoe UI", 12f, FontStyle.Bold);
            string text = L.Code == "ru" ? Russian : L.Code == "uz" ? Uzbek : English;
            foreach (string raw in text.Replace("\r", "").Split('\n'))
            {
                string line = raw.Trim();
                bool head = line.StartsWith("# ");
                box.SelectionFont = head ? heading : Font;
                box.SelectionColor = head ? Theme.Accent : Theme.Text;
                box.AppendText((head ? line.Substring(2) : line) + "\n");
            }
            box.Select(0, 0);
            Theme.Apply(this);
        }

        const string Russian = @"# Что это
Маленькое существо, которое летает за указателем мыши и оставляет за собой светящуюся пыльцу. Когда мышь не двигается, оно возвращается к кнопке «Пуск» и отдыхает там. Работе не мешает: все нажатия проходят сквозь него.

# Как открыть настройки
• Значок бабочки возле часов (если его не видно, нажмите стрелочку «^»): левый клик открывает настройки, правый — меню.
• Правый клик по пустому месту рабочего стола → «Бабочка — настройки».
Все изменения применяются сразу и сохраняются сами.

# Существа
В списке «Кто летает за мышью» есть бабочка, жук, паук, улитка, ниндзя с мечом, лучадор в маске, пиксельный коммандос, байкер, вертолёт, ударный вертолёт, слонёнок, лисичка, змея, панда-мастер, рука-помощница, облако с дождём, облако со снегом, солнце, луна и флаг. Список «Как двигается» задаёт способ движения: летает, ползает, скользит, парит, бежит или развевается, как флаг.
• Флаг своей страны выбирается в списке «Флаг страны» — там все страны мира.
• Ниндзя бежит за мышью, как в старых играх, а когда мышь стоит — останавливается с мечом.

# Свои картинки
Нажмите «Добавить картинку…» и выберите файл (JPG, PNG, BMP, GIF). Программа сама уберёт фон и добавит картинку в список.
• Лучше всего получаются картинки на ровном однотонном фоне, например белом. Пёстрый фон убрать не получится.
• Можно просто положить файлы в папку creatures рядом с программой — они превратятся в PNG автоматически.
• Название в списке — это имя файла.
• Чтобы убрать картинку из списка, удалите её файлы из папки creatures.

# Пыльца и свечение
Цвета пылинок вы выбираете сами: «+ Добавить цвет» открывает палитру, где можно указать любой цвет (в том числе числами RGB). Клик по цветному квадратику меняет цвет, правый клик — удаляет. Цветов может быть несколько — пылинки будут разноцветными. В списке «Готовый набор» есть готовые сочетания и радуга.
Ещё настраиваются количество, размер, яркость и время свечения пылинок, а также сияние вокруг самого существа и его цвет. Пыльцу можно выключить совсем.

# Поведение
«Скорость» — как быстро существо догоняет мышь. «Через сколько секунд покоя» — сколько оно ждёт, прежде чем улететь к «Пуску». Если экранов несколько, оно садится на том, где сейчас мышь.

# Развлечения
• «Демонстрация для видео» (в настройках и в меню значка) — существо само летает по экрану восьмёрками, мышь не нужна. Удобно записывать ролики. Выключается той же кнопкой.
• Реакция на клик — искры там, где вы щёлкнули, бабочка делает кувырок, ниндзя бросает сюрикен, коммандос прыгает кувырком, слонёнок брызгает водой.
• Сезонные эффекты — вместе с пыльцой летят снежинки зимой, лепестки сакуры весной, листья осенью, тыквы на Хэллоуин и конфетти на Новый год.
• Танец под музыку — когда играет звук, существо пританцовывает и пульсирует в такт. Программа только смотрит громкость, ничего не записывает.
• Ночное свечение — с 20:00 до 6:00 существо светится ярче.
Каждую функцию можно выключить галочкой в разделе «Развлечения».
Секреты: покрутите мышью быстрыми кругами — существо закружится и сядет вам на курсор. А если резко потрясти мышью — испугается и отлетит.

# Игры и видео
Когда игра или видео открыты на весь экран, существо само прячется и возвращается после выхода. Спрятать вручную: меню значка → «Спрятать».

# Программы, в которых существо прячется
Чтобы существо не отвлекало от работы, оно само прячется, пока активно окно одной из выбранных программ: Photoshop и другие программы Adobe, Zoom, Word, Excel, PowerPoint, Outlook, Teams и ещё несколько. Стоит переключиться в другое окно или свернуть программу — оно возвращается.
Что именно делать, выбираете вы: «Стать неактивной» — существо уменьшается до размера значка «Пуск» и тихо сидит рядом с ним (так сделано по умолчанию), или «Спрятаться» — оно полностью исчезает.
Список открывается кнопкой «Программы, в которых прятаться…» в настройках. Там можно снять галочку с любой программы, добавить свою (из уже запущенных или выбрав её файл) или выключить эту функцию целиком.

# Установка и удаление
При первом запуске программа предлагает установиться: вы выбираете папку, ярлык на рабочем столе и автозапуск. После установки она есть в меню «Пуск» и в «Параметры → Приложения». Можно и «Запустить без установки» — тогда она работает прямо из того места, где лежит файл.
Удалить: «Параметры → Приложения» → Butterfly Cursor → «Удалить». Программа удалит себя, свои настройки, ярлыки и картинки.
";

        const string English = @"# What it is
A small creature that follows your mouse pointer and leaves a trail of glowing dust. When the mouse is still, it goes back to the Start button and rests there. It never gets in the way: every click passes straight through it.

# How to open the settings
• The butterfly icon near the clock (if you cannot see it, click the “^” arrow): left-click opens the settings, right-click opens the menu.
• Right-click an empty spot on the desktop → “Butterfly — settings”.
Every change is applied at once and saved automatically.

# Creatures
The “Who follows the mouse” list has a butterfly, a beetle, a spider, a snail, a ninja with a sword, a masked luchador, a pixel commando, a biker, a helicopter, an attack helicopter, a baby elephant, a fox, a snake, a panda master, a helper hand, a rain cloud, a snow cloud, the sun, the moon and a flag. “How it moves” sets the way of moving: flies, crawls, glides, floats, runs or waves like a flag.
• Choose your country in the “Country flag” list — every country in the world is there.
• The ninja runs after the mouse like in old games and stops, sword in hand, when the mouse is still.

# Your own pictures
Press “Add picture…” and choose a file (JPG, PNG, BMP, GIF). The program removes the background by itself and adds the picture to the list.
• Pictures on a plain single-colour background, such as white, work best. A busy background cannot be removed.
• You can also simply drop files into the creatures folder next to the program — they are turned into PNG automatically.
• The name in the list is the file name.
• To remove a picture from the list, delete its files from the creatures folder.

# Fairy dust and glow
You choose the dust colours yourself: “+ Add colour” opens a palette where any colour can be set (including by RGB numbers). Click a colour square to change it, right-click to remove it. With several colours the dust is multicoloured. The “Ready-made set” list has prepared combinations and a rainbow.
You can also set the amount, size, brightness and glow time of the dust, and a glow around the creature itself with its own colour. The dust can be switched off completely.

# Behaviour
“Speed” is how fast the creature catches up with the mouse. “After how many idle seconds” is how long it waits before flying to the Start button. With several screens it lands on the one where the mouse is.

# Fun
• “Demo for videos” (in the settings and the icon menu) — the creature flies figure eights on its own, no mouse needed. Handy for recording clips. The same button stops it.
• React to clicks — sparks where you click, the butterfly does a somersault, the ninja throws a shuriken, the commando somersaults, the elephant sprays water.
• Seasonal effects — snowflakes in winter, sakura petals in spring, leaves in autumn, pumpkins at Halloween and confetti at New Year fly with the dust.
• Dance to music — while sound is playing, the creature dances and pulses to the beat. The program only looks at the volume, nothing is recorded.
• Night glow — from 20:00 to 6:00 the creature shines brighter.
Each of them can be switched off in the “Fun” section.
Secrets: draw fast circles with the mouse — the creature gets dizzy and sits on your pointer. Shake the mouse hard — it gets scared and flies off.

# Games and video
While a game or a video is full screen, the creature hides by itself and comes back when you leave. To hide it by hand: icon menu → “Hide”.

# Programs in which the creature hides
So that it does not distract you from work, the creature hides by itself while the window of one of the chosen programs is active: Photoshop and other Adobe programs, Zoom, Word, Excel, PowerPoint, Outlook, Teams and a few more. Switch to another window or minimise the program and it comes back.
You choose what exactly happens: “Go inactive” — the creature shrinks to the size of the Start icon and sits quietly next to it (the default), or “Hide” — it disappears completely.
The list opens with the “Programs to hide in…” button in the settings. There you can untick any program, add your own (from the ones running now or by choosing its file) or switch the feature off completely.

# Installing and removing
On the first start the program offers to install itself: you choose the folder, a desktop shortcut and starting with Windows. After that it is in the Start menu and in Settings → Apps. You can also press “Run without installing” — then it runs right where the file is.
To remove it: Settings → Apps → Butterfly Cursor → Uninstall. It removes itself, its settings, shortcuts and pictures.
";

        const string Uzbek = @"# Bu nima
Sichqoncha koʻrsatkichi ortidan uchib yuradigan va ortidan yaltiroq chang qoldiradigan kichkina jonzot. Sichqoncha qimirlamay tursa, u «Pusk» tugmasi yoniga qaytib, oʻsha yerda dam oladi. Ishga xalaqit bermaydi: barcha bosishlar uning ichidan oʻtib ketadi.

# Sozlamalarni qanday ochish
• Soat yonidagi kapalak belgisi (koʻrinmasa, «^» strelkasini bosing): chap tugma sozlamalarni, oʻng tugma menyuni ochadi.
• Ish stolining boʻsh joyida oʻng tugma → «Kapalak — sozlamalar».
Barcha oʻzgarishlar darhol qoʻllanadi va oʻzi saqlanadi.

# Jonzotlar
«Sichqoncha ortidan kim yuradi» roʻyxatida kapalak, qoʻngʻiz, oʻrgimchak, shilliqqurt, qilichli ninja, niqobli luchador, piksel komandos, bayker, vertolyot, hujumchi vertolyot, fil bolasi, tulkicha, ilon, panda usta, yordamchi qoʻl, yomgʻirli bulut, qorli bulut, quyosh, oy va bayroq bor. «Qanday harakatlanadi» roʻyxati harakat turini belgilaydi: uchadi, oʻrmalaydi, sirpanadi, havoda suzadi, yuguradi yoki bayroqdek hilpiraydi.
• Oʻz davlatingiz bayrogʻini «Davlat bayrogʻi» roʻyxatidan tanlang — u yerda dunyoning barcha davlatlari bor.
• Ninja eski oʻyinlardagidek sichqoncha ortidan yuguradi, sichqoncha toʻxtasa — qilichini ushlab toʻxtaydi.

# Oʻz rasmlaringiz
«Rasm qoʻshish…» tugmasini bosing va faylni tanlang (JPG, PNG, BMP, GIF). Dastur fonni oʻzi olib tashlaydi va rasmni roʻyxatga qoʻshadi.
• Bir xil rangli tekis fondagi, masalan oq fondagi rasmlar eng yaxshi chiqadi. Rang-barang fonni olib tashlab boʻlmaydi.
• Fayllarni dastur yonidagi creatures papkasiga shunchaki tashlab qoʻysangiz ham boʻladi — ular avtomatik ravishda PNG ga aylanadi.
• Roʻyxatdagi nom — bu fayl nomi.
• Rasmni roʻyxatdan olib tashlash uchun uning fayllarini creatures papkasidan oʻchiring.

# Sehrli chang va yogʻdu
Zarrachalar ranglarini oʻzingiz tanlaysiz: «+ Rang qoʻshish» tugmasi istalgan rangni (RGB raqamlari bilan ham) tanlash mumkin boʻlgan palitrani ochadi. Rangli kvadratni bossangiz — rang oʻzgaradi, oʻng tugma bilan bossangiz — oʻchadi. Ranglar bir nechta boʻlsa, zarrachalar rang-barang boʻladi. «Tayyor toʻplam» roʻyxatida tayyor birikmalar va kamalak bor.
Shuningdek zarrachalarning soni, oʻlchami, yorqinligi va yonish vaqtini, jonzot atrofidagi yogʻdu va uning rangini sozlash mumkin. Changni butunlay oʻchirib qoʻysa ham boʻladi.

# Xatti-harakat
«Tezlik» — jonzot sichqonchaga qanchalik tez yetib olishi. «Necha soniya kutgandan keyin» — «Pusk» tugmasiga uchishdan oldin qancha kutishi. Ekran bir nechta boʻlsa, u sichqoncha turgan ekranga qoʻnadi.

# Koʻngilochar
• «Video uchun namoyish» (sozlamalarda va belgi menyusida) — jonzot ekranda oʻzi sakkizlik chizib uchadi, sichqoncha kerak emas. Video yozish uchun qulay. Xuddi shu tugma bilan toʻxtatiladi.
• Bosishga javob — bosgan joyingizda uchqunlar, kapalak umbaloq oshadi, ninja shuriken otadi, komandos umbaloq oshib sakraydi, fil bolasi suv sepadi.
• Mavsumiy effektlar — chang bilan birga qishda qor parchalari, bahorda sakura gulbarglari, kuzda barglar, Xellouinda qovoqlar va Yangi yilda konfetti uchadi.
• Musiqaga raqs — ovoz yangraganda jonzot ritmga mos raqs tushadi. Dastur faqat ovoz balandligini kuzatadi, hech narsa yozib olinmaydi.
• Tungi yogʻdu — 20:00 dan 6:00 gacha jonzot yorqinroq porlaydi.
Har birini «Koʻngilochar» boʻlimida oʻchirib qoʻyish mumkin.
Sirlar: sichqonchani tez aylantiring — jonzotning boshi aylanib, kursoringizga oʻtirib oladi. Sichqonchani keskin silkitsangiz — qoʻrqib, uchib ketadi.

# Oʻyinlar va video
Oʻyin yoki video toʻliq ekranda ochilganda jonzot oʻzi yashirinadi va siz chiqqaningizdan keyin qaytadi. Qoʻlda yashirish: belgi menyusi → «Yashirish».

# Jonzot yashirinadigan dasturlar
Ishdan chalgʻitmasligi uchun, tanlangan dasturlardan birining oynasi faol boʻlganda jonzot oʻzi yashirinadi: Photoshop va boshqa Adobe dasturlari, Zoom, Word, Excel, PowerPoint, Outlook, Teams va yana bir nechtasi. Boshqa oynaga oʻtsangiz yoki dasturni yigʻib qoʻysangiz — u qaytib keladi.
Aynan nima boʻlishini oʻzingiz tanlaysiz: «Nofaol boʻlish» — jonzot «Pusk» belgisi oʻlchamigacha kichrayib, uning yonida jimgina oʻtiradi (standart holat), yoki «Yashirinish» — u butunlay gʻoyib boʻladi.
Roʻyxat sozlamalardagi «Yashirinadigan dasturlar…» tugmasi bilan ochiladi. U yerda istalgan dasturdan belgini olib tashlash, oʻz dasturingizni qoʻshish (ishlab turganlaridan yoki faylini tanlab) yoki bu funksiyani butunlay oʻchirib qoʻyish mumkin.

# Oʻrnatish va oʻchirish
Birinchi ishga tushirishda dastur oʻrnatishni taklif qiladi: papkani, ish stolidagi yorliqni va Windows bilan birga ishga tushishni oʻzingiz tanlaysiz. Shundan soʻng u «Pusk» menyusida va «Sozlamalar → Ilovalar» boʻlimida boʻladi. «Oʻrnatmasdan ishga tushirish» ni ham tanlash mumkin — unda dastur fayl turgan joyning oʻzida ishlaydi.
Oʻchirish: «Sozlamalar → Ilovalar» → Butterfly Cursor → «Oʻchirish». Dastur oʻzini, sozlamalarini, yorliqlarini va rasmlarini oʻchiradi.
";
    }
}
