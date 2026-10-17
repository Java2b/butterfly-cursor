using System.Collections.Generic;
using System.Globalization;

namespace ButterflyCursor
{
    /// <summary>Interface texts. Russian is the source text; this table adds English and Uzbek.</summary>
    static class L
    {
        public static readonly string[] Codes = { "", "ru", "en", "uz" };
        public static readonly string[] Names = { "Авто (как в Windows)", "Русский", "English", "Oʻzbekcha" };

        /// <summary>Language in use: the chosen one, or the Windows display language.</summary>
        public static string Code
        {
            get
            {
                if (Cfg.Lang == "ru" || Cfg.Lang == "en" || Cfg.Lang == "uz") return Cfg.Lang;
                string sys = CultureInfo.CurrentUICulture.TwoLetterISOLanguageName;
                return sys == "ru" || sys == "uz" ? sys : "en";
            }
        }

        public static string T(string ru)
        {
            string code = Code;
            string[] tr;
            if (code == "ru" || !Table.TryGetValue(ru, out tr)) return ru;
            return code == "uz" ? tr[1] : tr[0];
        }

        static readonly Dictionary<string, string[]> Table = new Dictionary<string, string[]>
        {
            // tray and desktop menu
            { "Настройки…", new[] { "Settings…", "Sozlamalar…" } },
            { "Существо", new[] { "Creature", "Jonzot" } },
            { "Спрятать", new[] { "Hide", "Yashirish" } },
            { "Выход", new[] { "Exit", "Chiqish" } },
            { "Бабочка — правый клик: настройки", new[] { "Butterfly — right-click for settings", "Kapalak — oʻng tugma: sozlamalar" } },
            { "Бабочка — настройки", new[] { "Butterfly — settings", "Kapalak — sozlamalar" } },

            // creatures
            { "Бабочка", new[] { "Butterfly", "Kapalak" } },
            { "Жук", new[] { "Beetle", "Qoʻngʻiz" } },
            { "Паук", new[] { "Spider", "Oʻrgimchak" } },
            { "Улитка", new[] { "Snail", "Shilliqqurt" } },
            { "Кто летает за мышью", new[] { "Who follows the mouse", "Sichqoncha ortidan kim yuradi" } },
            { "Как двигается", new[] { "How it moves", "Qanday harakatlanadi" } },
            { "Летает (машет крыльями)", new[] { "Flies (flaps its wings)", "Uchadi (qanot qoqadi)" } },
            { "Ползает (вид сверху)", new[] { "Crawls (top view)", "Oʻrmalaydi (tepadan koʻrinish)" } },
            { "Скользит, как улитка (вид сбоку)", new[] { "Glides like a snail (side view)", "Shilliqqurtdek sirpanadi (yondan koʻrinish)" } },
            { "Парит (не поворачивается)", new[] { "Floats (stays upright)", "Havoda suzadi (burilmaydi)" } },
            { "Размер", new[] { "Size", "Oʻlcham" } },
            { "Добавить свою картинку (папка creatures)…", new[] { "Add your own picture (creatures folder)…", "Oʻz rasmingizni qoʻshish (creatures papkasi)…" } },

            { "Добавить картинку…", new[] { "Add picture…", "Rasm qoʻshish…" } },
            { "Открыть папку с картинками", new[] { "Open the pictures folder", "Rasmlar papkasini ochish" } },
            { "Картинки", new[] { "Pictures", "Rasmlar" } },
            { "Не получилось обработать картинку:", new[] { "Could not process the picture:", "Rasmni qayta ishlab boʻlmadi:" } },
            { "Инструкция", new[] { "Help", "Qoʻllanma" } },
            { "Бабочка — инструкция", new[] { "Butterfly — help", "Kapalak — qoʻllanma" } },

            { "Ниндзя", new[] { "Ninja", "Ninja" } },
            { "Флаг", new[] { "Flag", "Bayroq" } },
            { "Флаг страны", new[] { "Country flag", "Davlat bayrogʻi" } },
            { "Бежит (вид сбоку, по кадрам)", new[] { "Runs (side view, frame by frame)", "Yuguradi (yondan, kadrma-kadr)" } },
            { "Развевается, как флаг", new[] { "Waves like a flag", "Bayroqdek hilpiraydi" } },

            // installer
            { "Бабочка — установка", new[] { "Butterfly — setup", "Kapalak — oʻrnatish" } },
            { "Бабочка, которая летает за мышью", new[] { "A butterfly that follows your mouse", "Sichqoncha ortidan uchadigan kapalak" } },
            { "Куда установить программу?", new[] { "Where should the program be installed?", "Dasturni qayerga oʻrnatish kerak?" } },
            { "Обзор…", new[] { "Browse…", "Tanlash…" } },
            { "Ярлык на рабочем столе", new[] { "Desktop shortcut", "Ish stolida yorliq" } },
            { "Программа появится в меню «Пуск» и в «Параметры → Приложения», откуда её можно удалить.", new[] { "The program will appear in the Start menu and in Settings → Apps, where it can be uninstalled.", "Dastur «Pusk» menyusida va «Sozlamalar → Ilovalar» boʻlimida paydo boʻladi, u yerdan uni oʻchirish mumkin." } },
            { "Больше не спрашивать", new[] { "Don’t ask again", "Boshqa soʻramaslik" } },
            { "Установить", new[] { "Install", "Oʻrnatish" } },
            { "Запустить без установки", new[] { "Run without installing", "Oʻrnatmasdan ishga tushirish" } },
            { "Не получилось установить:", new[] { "Could not install:", "Oʻrnatib boʻlmadi:" } },
            { "Удалить «Бабочку» с компьютера? Будут удалены программа, её настройки и картинки из папки creatures.", new[] { "Remove Butterfly from this computer? The program, its settings and the pictures in the creatures folder will be deleted.", "«Kapalak» kompyuterdan oʻchirilsinmi? Dastur, uning sozlamalari va creatures papkasidagi rasmlar oʻchiriladi." } },
            { "«Бабочка» удалена.", new[] { "Butterfly has been removed.", "«Kapalak» oʻchirildi." } },

            { "Рука-помощница", new[] { "Helper hand", "Yordamchi qoʻl" } },
            { "Развлечения", new[] { "Fun", "Koʻngilochar" } },
            { "Реакция на клик: искры, кувырок, ниндзя бросает сюрикен", new[] { "React to clicks: sparks, a somersault, the ninja throws a shuriken", "Bosishga javob: uchqunlar, umbaloq, ninja shuriken otadi" } },
            { "Сезонные эффекты: снег, листья, сакура, праздники", new[] { "Seasonal effects: snow, leaves, sakura, holidays", "Mavsumiy effektlar: qor, barglar, sakura, bayramlar" } },
            { "Танцевать под музыку", new[] { "Dance to music", "Musiqaga raqs tushish" } },
            { "Ночное свечение: вечером и ночью светится ярче", new[] { "Night glow: shines brighter in the evening and at night", "Tungi yogʻdu: kechqurun va tunda yorqinroq porlaydi" } },
            { "▶ Демонстрация для видео", new[] { "▶ Demo for videos", "▶ Video uchun namoyish" } },
            { "■ Остановить демонстрацию", new[] { "■ Stop the demo", "■ Namoyishni toʻxtatish" } },
            { "Демонстрация для видео", new[] { "Demo for videos", "Video uchun namoyish" } },

            { "Облако с дождём", new[] { "Rain cloud", "Yomgʻirli bulut" } },
            { "Облако со снегом", new[] { "Snow cloud", "Qorli bulut" } },
            { "Солнце", new[] { "Sun", "Quyosh" } },
            { "Луна", new[] { "Moon", "Oy" } },

            { "Лучадор «Бабочка»", new[] { "Luchador “Mariposa”", "Luchador «Kapalak»" } },

            { "Дракон", new[] { "Dragon", "Ajdaho" } },
            { "Голова льва", new[] { "Lion head", "Sher boshi" } },
            { "Слонёнок", new[] { "Baby elephant", "Fil bolasi" } },
            { "Панда-мастер", new[] { "Panda master", "Panda usta" } },

            { "Все", new[] { "All", "Hammasi" } },
            { "Насекомые", new[] { "Insects", "Hasharotlar" } },
            { "Животные", new[] { "Animals", "Hayvonlar" } },
            { "Герои", new[] { "Heroes", "Qahramonlar" } },
            { "Фэнтези", new[] { "Fantasy", "Fantastika" } },
            { "Погода", new[] { "Weather", "Ob-havo" } },
            { "Флаги", new[] { "Flags", "Bayroqlar" } },
            { "Мои картинки", new[] { "My pictures", "Mening rasmlarim" } },
            { "Светлая / тёмная тема", new[] { "Light / dark theme", "Yorugʻ / qorongʻi mavzu" } },
            { "Свои картинки появятся в разделе «Мои картинки»", new[] { "Your pictures appear under “My pictures”", "Rasmlaringiz «Mening rasmlarim» boʻlimida paydo boʻladi" } },
            { "Здесь пока пусто — добавьте свою картинку кнопкой ниже.", new[] { "Nothing here yet — add your own picture with the button below.", "Hozircha boʻsh — quyidagi tugma bilan oʻz rasmingizni qoʻshing." } },
            { "Ваша картинка из папки creatures", new[] { "Your picture from the creatures folder", "creatures papkasidagi rasmingiz" } },
            { "Порхает за мышью и оставляет волшебную пыльцу", new[] { "Flutters after the mouse leaving magic dust", "Sichqoncha ortidan uchib, sehrli chang qoldiradi" } },
            { "Деловито ползает и покачивается на ходу", new[] { "Crawls busily, swaying as it goes", "Chaqqon oʻrmalaydi, yurganda chayqaladi" } },
            { "Быстро перебирает лапками", new[] { "Scurries along on eight legs", "Oyoqchalarini tez-tez bosadi" } },
            { "Медленно, но верно ползёт к курсору", new[] { "Slowly but surely creeps to the pointer", "Sekin, lekin aniq kursor tomon oʻrmalaydi" } },
            { "Бежит с мечом, в покое медитирует на «Пуске»", new[] { "Runs with a sword, meditates on Start when idle", "Qilich bilan yuguradi, dam olganda «Pusk» ustida meditatsiya qiladi" } },
            { "Бегает на кончиках пальцев", new[] { "Scuttles on its fingertips", "Barmoq uchlarida yuguradi" } },
            { "Рестлер в маске, в покое играет мышцами", new[] { "A masked wrestler who flexes when idle", "Niqobli kurashchi, dam olganda muskullarini oʻynatadi" } },
            { "Летает и машет крыльями, в покое спит калачиком", new[] { "Flies flapping its wings, sleeps curled up when idle", "Qanot qoqib uchadi, dam olganda yumaloq boʻlib uxlaydi" } },
            { "Парит рядом, моргает и иногда рычит", new[] { "Floats nearby, blinks and roars now and then", "Yonida suzadi, koʻz qisadi va baʻzan oʻkiradi" } },
            { "Топает и играет хоботом", new[] { "Stomps along and plays with its trunk", "Tap-tap yuradi va xartumi bilan oʻynaydi" } },
            { "Ходит вразвалку, в покое ест бамбук", new[] { "Waddles along, eats bamboo when idle", "Lapanglab yuradi, dam olganda bambuk yeydi" } },
            { "Летает за мышью и поливает дождиком", new[] { "Follows the mouse and sprinkles rain", "Sichqoncha ortidan uchib, yomgʻir sepadi" } },
            { "Тихо сыплет снежинки", new[] { "Quietly lets snowflakes fall", "Sekingina qor parchalarini sochadi" } },
            { "Светит и медленно вращает лучами", new[] { "Shines and slowly turns its rays", "Charaqlaydi va nurlarini sekin aylantiradi" } },
            { "Полумесяц, вокруг мерцают звёзды", new[] { "A crescent with twinkling stars around", "Yarim oy, atrofida yulduzlar miltillaydi" } },
            { "Флаг вашей страны развевается на ветру", new[] { "Your country's flag waving in the wind", "Davlatingiz bayrogʻi shamolda hilpiraydi" } },

            // behaviour
            { "Поведение", new[] { "Behaviour", "Xatti-harakat" } },
            { "Скорость", new[] { "Speed", "Tezlik" } },
            { "Возвращаться к кнопке «Пуск», когда мышь не двигается", new[] { "Return to the Start button when the mouse is still", "Sichqoncha qimirlamasa, «Pusk» tugmasiga qaytish" } },
            { "Через сколько секунд покоя", new[] { "After how many idle seconds", "Necha soniya kutgandan keyin" } },
            { "Прятаться, когда игра или видео открыты на весь экран", new[] { "Hide while a game or video is full screen", "Oʻyin yoki video toʻliq ekranda boʻlsa, yashirinish" } },

            { "Программы, в которых прятаться…", new[] { "Programs to hide in…", "Yashirinadigan dasturlar…" } },
            { "Бабочка — программы", new[] { "Butterfly — programs", "Kapalak — dasturlar" } },
            { "Пока одна из отмеченных программ открыта и активна, существо уходит в сторону. Как только вы переключаетесь в другое окно, оно возвращается.", new[] { "While one of the ticked programs is open and active, the creature steps aside. As soon as you switch to another window, it comes back.", "Belgilangan dasturlardan biri ochiq va faol boʻlsa, jonzot chetga chiqadi. Boshqa oynaga oʻtishingiz bilan u qaytib keladi." } },
            { "Прятаться в отмеченных программах", new[] { "Hide in the ticked programs", "Belgilangan dasturlarda yashirinish" } },
            { "Добавить запущенную программу…", new[] { "Add a running program…", "Ishlab turgan dasturni qoʻshish…" } },
            { "Выбрать файл программы…", new[] { "Choose a program file…", "Dastur faylini tanlash…" } },
            { "Удалить из списка", new[] { "Remove from the list", "Roʻyxatdan oʻchirish" } },
            { "Программы", new[] { "Programs", "Dasturlar" } },
            { "(добавлено вами)", new[] { "(added by you)", "(siz qoʻshgansiz)" } },

            { "Что делать в этих программах:", new[] { "What to do in these programs:", "Bu dasturlarda nima qilsin:" } },
            { "Стать неактивной: уменьшиться и сидеть у кнопки «Пуск»", new[] { "Go inactive: shrink and sit by the Start button", "Nofaol boʻlish: kichrayib, «Pusk» tugmasi yonida oʻtirish" } },
            { "Спрятаться: полностью исчезнуть", new[] { "Hide: disappear completely", "Yashirinish: butunlay gʻoyib boʻlish" } },

            // dust
            { "Пыльца и свечение", new[] { "Fairy dust and glow", "Sehrli chang va yogʻdu" } },
            { "Оставлять за собой светящуюся пыльцу", new[] { "Leave a trail of glowing dust", "Ortidan yaltiroq chang qoldirish" } },
            { "Цвет", new[] { "Colour", "Rang" } },
            { "Выбрать…", new[] { "Choose…", "Tanlash…" } },
            { "Волшебная (разноцветная)", new[] { "Magic (multicolour)", "Sehrli (rang-barang)" } },
            { "Голубая", new[] { "Blue", "Havorang" } },
            { "Золотая", new[] { "Gold", "Tilla rang" } },
            { "Розовая", new[] { "Pink", "Pushti" } },
            { "Зелёная", new[] { "Green", "Yashil" } },
            { "Радуга", new[] { "Rainbow", "Kamalak" } },
            { "Свой цвет", new[] { "Custom colour", "Oʻz rangingiz" } },
            { "Цвета пылинок", new[] { "Dust colours", "Zarrachalar ranglari" } },
            { "+ Добавить цвет", new[] { "+ Add colour", "+ Rang qoʻshish" } },
            { "Клик — изменить цвет, правый клик — удалить", new[] { "Click to change the colour, right-click to remove it", "Bosish — rangni oʻzgartirish, oʻng tugma — oʻchirish" } },
            { "Готовый набор", new[] { "Ready-made set", "Tayyor toʻplam" } },
            { "Свои цвета", new[] { "My colours", "Oʻz ranglarim" } },
            { "Цвет сияния", new[] { "Glow colour", "Yogʻdu rangi" } },
            { "Количество пылинок", new[] { "Amount of dust", "Zarrachalar soni" } },
            { "Размер пылинок", new[] { "Dust size", "Zarrachalar oʻlchami" } },
            { "Как долго светятся", new[] { "How long it glows", "Qancha vaqt yonadi" } },
            { "Яркость", new[] { "Brightness", "Yorqinlik" } },
            { "Сияние вокруг существа", new[] { "Glow around the creature", "Jonzot atrofidagi yogʻdu" } },

            // misc
            { "Прочее", new[] { "Other", "Boshqa" } },
            { "Язык", new[] { "Language", "Til" } },
            { "Авто (как в Windows)", new[] { "Auto (same as Windows)", "Avto (Windows tili)" } },
            { "Запускать вместе с Windows", new[] { "Start with Windows", "Windows bilan birga ishga tushirish" } },
            { "Пункт «Бабочка — настройки» в меню рабочего стола (правый клик)", new[] { "“Butterfly — settings” item in the desktop right-click menu", "Ish stoli menyusida «Kapalak — sozlamalar» bandi (oʻng tugma)" } },
            { "Закрыть", new[] { "Close", "Yopish" } },
            { "По умолчанию", new[] { "Defaults", "Standart holat" } },
        };
    }
}
