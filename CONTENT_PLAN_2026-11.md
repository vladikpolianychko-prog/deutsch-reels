# Запас контенту 23.10 – 30.11.2026 (карусель 10:00 + рілс 14:00 щодня)

## Ліміт Metricool Free
- 20 ОПУБЛІКОВАНИХ постів на календарний місяць (заплановані й чернетки не рахуються; лічильник обнуляється 1-го). Понад 20 Metricool дає запланувати, але НЕ публікує до наступного місяця. Лічильник видно в планувальнику Metricool. API лічильника не віддає, тож рахуємо самі: getScheduledPosts за місяць → пости з draft=false, статус PUBLISHED або PENDING.
- Жовтень: до 22.10 включно ~16 (15 опубліковано + рілс 22.10 14:00). Лишається ~4 → 23.10 і 24.10 (карусель + рілс). З 25.10 до 31.10 — у Metricool НЕ ставимо, складаємо в outbox/.
- Листопад: 20 постів = 1–10.11 (карусель + рілс). 11–30.11 — в outbox/ до підключення іншого сервісу.

## Сховище (outbox) для постів, які не влазять у Metricool
`outbox/YYYY-MM-DD/`: `carousel/slide1..N.png`, `reel.mp4`, `post.json` ({"date","carousel":{"time":"10:00","caption","first_comment","alt":[]},"reel":{"time":"14:00","caption","first_comment","cover_ms":300}}). Загальний список: `outbox/MANIFEST.md` (дата, тема, що готово, де заплановано). Файли беруться напряму з GitHub (raw.githubusercontent.com/vladikpolianychko-prog/deutsch-reels/main/outbox/...), тож будь-який сервіс або ручна публікація з телефона їх підхопить.

## Теми (усі на перевірених значеннях; тренди — RESEARCH_TRENDS_2026-10.md)
| Дата | Тема (ключове слово для PDF) | Карусель: подача | Рілс: подача |
|---|---|---|---|
| Пт 23.10 | Помилки-привиди: Mir ist kalt / Ich bin 35 / Ich bin fertig / Ich hätte gern (GHOST) | Things you should ghost 👻 | зім'ятий аркуш |
| Сб 24.10 | Довгі слова: як розбирати (LANG) | розбір на частини | My reaction to ___ (наростання) — текстом на аркуші |
| Нд 25.10 | Zeitumstellung сьогодні: Winterzeit, zurückstellen (ZEIT) | How to avoid stress (мем) | зім'ятий аркуш |
| Пн 26.10 | Моя німецька 2016 vs 2026: Hände hoch → Termin, Bescheid (2016) | тоді / зараз | ностальгія, аркуш |
| Вт 27.10 | doch (DOCH) | WTF is doch?! | аркуш: 3 значення doch |
| Ср 28.10 | Mir ist heiß ≠ Ich bin heiß (HEISS) | Message from Deutsch… -D | аркуш |
| Чт 29.10 | Як вчити: щодня / щотижня / щомісяця (PLAN) | Once a day/week/month | аркуш-чекліст |
| Пт 30.10 | Halloween: Süßes oder Saures, sich verkleiden, der Kürbis (BOO) | «Чутливий контент» №2 | аркуш |
| Сб 31.10 | Feiertag / Ferien / Urlaub / frei (FREI) | Не плутай! | аркуш |
| Нд 01.11 | Termin / Frist / Datum / Verabredung (TERMIN) | «це НЕ» хук | аркуш |
| Пн 02.11 | Brief vom Amt: Bescheid, Widerspruch, Frist (BRIEF) | How to avoid stress | аркуш |
| Вт 03.11 | Mir ist kalt — Heizung, lüften, Heizkosten (KALT) | Message from Deutsch | аркуш |
| Ср 04.11 | Beim Arzt: Schmerzen, weh tun, Krankschreibung (ARZT) | ghost-помилки | аркуш |
| Чт 05.11 | bekommen ≠ become, also ≠ also, Chef ≠ шеф-кухар (FALSE) | Не плутай! (хибні друзі) | аркуш |
| Пт 06.11 | Pfand: Flasche zurückgeben, Pfandautomat (PFAND) | «це НЕ» хук | аркуш |
| Сб 07.11 | Bäckerei: Brötchen, Semmel, Schrippe, belegt (BROT) | regional: одне слово — 3 назви | аркуш |
| Нд 08.11 | Sonntag: alles zu, geschlossen, Ruhetag, Spätkauf (ZU) | How to avoid stress | аркуш |
| Пн 09.11 | 9. November / Mauerfall: die Mauer, die Wende, wiedervereinigt (MAUER) | факти-карусель | аркуш |
| Вт 10.11 | St. Martin у Kita: Laterne, Laternenumzug, basteln (LATERNE) | чекліст для батьків | аркуш |
| Ср 11.11 | 11.11 о 11:11: Karneval / Fasching / Fastnacht (HELAU) | «чутливий контент» №3 або ghost | аркуш |
| Чт 12.11 | Wetter: nieseln, Glatteis, Schmuddelwetter (WETTER) | My reaction to ___ | аркуш |
| Пт 13.11 | Ich bin fertig: готова ≠ виснажена (FERTIG) | Message from Deutsch | аркуш |
| Сб 14.11 | gleich / sofort / bald / später (GLEICH) | Не плутай! | аркуш |
| Нд 15.11 | Bahn: Verspätung, Gleis, umsteigen, Zugausfall (BAHN) | How to avoid stress | аркуш |
| Пн 16.11 | Bürgeramt: anmelden, ummelden, Meldebescheinigung (AMT) | «це НЕ» хук | аркуш |
| Вт 17.11 | du oder Sie? duzen / siezen (DU) | 2 колонки | аркуш |
| Ср 18.11 | Arbeit: Mahlzeit!, Feierabend, Schönen Feierabend (MAHLZEIT) | WTF is Mahlzeit | аркуш |
| Чт 19.11 | Sich krankmelden (Arbeit, Kita) (KRANK) | чекліст-фрази | аркуш |
| Пт 20.11 | Black Friday: Angebot, Rabatt, reduziert, Schnäppchen (ANGEBOT) | My reaction to ___ (знижки) | аркуш |
| Сб 21.11 | Wohnung: Nebenkosten, Kaution, Warmmiete/Kaltmiete (MIETE) | Не плутай! | аркуш |
| Нд 22.11 | Telefonieren: buchstabieren, Rückruf, verbinden (TEL) | ghost-помилки | аркуш |
| Пн 23.11 | Weihnachtsmarkt: Glühwein, Bratwurst, Lebkuchen, Pfand für Tasse (MARKT) | факти-карусель | аркуш |
| Вт 24.11 | Elternsprechtag / Schule: Lehrer, Note, Hausaufgaben (SCHULE) | «це НЕ» хук | аркуш |
| Ср 25.11 | Komplimente: schön, hübsch, nett ≠ «нетто» (NETT) | Не плутай! | аркуш |
| Чт 26.11 | Small Talk: Wie geht's? — ehrlich antworten? (SMALL) | How to avoid stress | аркуш |
| Пт 27.11 | Adventskalender, Kerze, der Advent (ADVENT) | факти + словник | аркуш |
| Сб 28.11 | Einkaufen: Kasse, Kassenbon, Beutel, «Mit Karte?» (KASSE) | ghost-помилки | аркуш |
| Нд 29.11 | 1. Advent: Adventskranz, Plätzchen backen (KRANZ) | словник-карусель | аркуш |
| Пн 30.11 | Підсумок місяця: 10 слів-пасток листопада (TOP10) | рейтинг 10 | аркуш-рейтинг |

Правила: хуки — з RESEARCH_TRENDS_2026-10.md розділ 6 (бібліотека хуків), не повторювати частіше ніж раз на 7 днів; 1–2 рази на тиждень подачу каруселі замінювати на «N готових фраз для <ситуація>» (такі списки найбільше пересилають); тема рілса = тема каруселі; відповідь у рілсі до 3-ї с; CTA на відправлення («Скинь тому, хто …») + ключове слово для PDF (власник сам надсилає PDF у директ); без вигаданої статистики; кожен німецький приклад перевіряти. Подачу дозволено міняти за аналітикою (що дало більше поширень/збережень), записуючи причину в analytics_log.md.
