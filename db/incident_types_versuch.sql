
INSERT INTO incident_types (code, name, description, prompt_ref)
VALUES
/* ======================
   EINBRUCH
   ====================== */
('einbruch', 'Einbruch',
$$Definition: Unbefugtes gewaltsames Öffnen, Aufbrechen oder Eindringen in gesicherte Bereiche oder Behältnisse.

Typische Begriffe & Formulierungen:
"aufgebrochen"
"gewaltsam geöffnet"
"eingedrungen"
"Tür/Spind/Schrank aufgehebelt"
"Schloss manipuliert"
"mit Werkzeug aufgemacht"
"Einbruch in Werkstatt/Lagerraum"
"Verriegelung aufgebogen"
"versuchte Tür zu knacken"
"in den gesicherten Bereich gelangt"
"Spindschloss zerstört"

Beispiele:
"Spind eines anderen Insassen aufgebrochen."
"Versuchte mit Besteck das Türschloss zu öffnen."
"Er ist unbefugt in den Reinigungsraum eingedrungen."
$$,
'prompt_einbruch_v1'),

/* ======================
   SACHBESCHÄDIGUNG
   ====================== */
('sachbeschaedigung', 'Sachbeschädigung',
$$Definition: Absichtliche oder grob fahrlässige Beschädigung, Zerstörung oder massive Verunreinigung von Anstaltsoder Privateigentum.

Typische Begriffe & Formulierungen:
"zerstört"
"kaputt gemacht"
"eingeschlagen"
"zerrissen"
"verunstaltet"
"beschmiert"
"eingetreten"
"aus der Verankerung gerissen"
"Zelle verwüstet"
"Gegenstand mutwillig beschädigt"
"Toilette verstopft mit Absicht"
"Porzellan zerbrochen"
"Scheibe/Glas beschädigt"
"Fernseher manipuliert"
"Bett zerstört"
"Wände beschmiert"
"Kamera verdeckt / zerstört"
"Einrichtung zerrissen/zerlegt"

Beispiele:
"Fenster eingeschlagen."
"WC mit Kleidung verstopft, absichtlich."
"Er riss den Fernseher aus der Halterung."
"Zelle komplett verwüstet."
$$,
'prompt_sach_v1'),

/* ======================
   KÖRPERVERLETZUNG
   ====================== */
('koerperverletzung', 'Körperverletzung',
$$Definition: Jede Form physischer Gewalt oder körperlicher Einwirkung gegen eine Person (Insasse ↔ Insasse oder Insasse ↔ Bediensteter).

Typische Begriffe & Formulierungen:
"geschlagen"
"eine verpasst"
"ins Gesicht geboxt"
"getreten"
"gewürgt"
"gepackt / geschubst"
"an den Haaren gezogen"
"gebissen"
"mit Gegenstand geschlagen"
"attackiert"
"angegriffen"
"körperlich angegangen"
"Kopfstoß gegeben"
"auf den anderen losgegangen"
"Handgreiflichkeiten" (klar beschrieben!)
"Bediensteten verletzt"

Beispiele:
"Er schlug dem Bediensteten mit der Faust auf die Brust."
"Zwei Insassen gerieten in eine Schlägerei."
"Er würgte seinen Zellengenossen."
$$,
'prompt_koerp_v1'),

/* ======================
   BRANDSTIFTUNG
   ====================== */
('brandstiftung', 'Brandstiftung',
$$Definition: Jede Handlung, bei der ein Insasse oder eine andere Person bewusst oder fahrlässig etwas entzündet, verbrennt, schmoren lässt oder Feuer verursacht.

Typische Begriffe & Formulierungen:
"etwas angezündet"
"in Brand gesetzt"
"Feuer gelegt"
"Papier angezündet"
"Matratze brennt"
"offenes Feuer"
"Rauchentwicklung durch Handlung"
"Mülleimer brennt"
"Kleidung angezündet"

Beispiele:
"Insasse hat Klopapier angezündet."
"Matratze angezündet."
"Papier im Abfalleimer angezündet."
$$,
'prompt_brand_v1'),

/* ======================
   SELBSTVERLETZUNG
   ====================== */
('selbstverletzung', 'Selbstverletzung',
$$Definition: Jede absichtliche Selbstschädigung, unabhängig davon, ob sie oberflächlich oder schwer ist.

Typische Begriffe & Formulierungen:
"geritzt"
"geschnitten"
"sich verletzt"
"kopf gegen wand geschlagen"
"versucht sich zu erhängen"
"Ligatur angelegt"
"mit Klinge verletzt"
"Gegenstand verschluckt (absichtlich)"

Beispiele:
"Er hat sich am Unterarm geritzt."
"Kopf mehrfach gegen die Wand geschlagen."
"Versuch der Selbststrangulation."
$$,
'prompt_selbst_v1'),

/* ======================
   DIEBSTAHL
   ====================== */
('diebstahl', 'Diebstahl',
$$Definition: Wegnahme oder Aneignung fremden Eigentums — durch Insassen oder Bedienstete.

Typische Begriffe & Formulierungen:
"gestohlen"
"entwendet"
"weggenommen"
"geklaut"
"unerlaubt an sich genommen"
"eingesteckt"

Beispiele:
"Er hat Zigaretten gestohlen."
"Geldbörse aus Spind entwendet."
$$,
'prompt_diebstahl_v1'),

/* ======================
   BEDROHUNG
   ====================== */
('bedrohung', 'Bedrohung',
$$Definition: Aussprechen oder Androhen von Gewalt ohne unmittelbare körperliche Einwirkung.

Beispiele:
"Ich bring dich um!"
"Du wirst schon sehen, was passiert!"

$$,
'prompt_bedrohung_v1'),

/* ======================
   NÖTIGUNG
   ====================== */
('noetigung', 'Nötigung',
$$Definition: Zwang zur Handlung, Duldung oder Unterlassung ohne direkte Gewaltanwendung.

Beispiele:
"Gib mir deine Zigaretten, sonst bekommst du Probleme."
"Mach das für mich, sonst passiert etwas."
$$,
'prompt_noetigung_v1'),

/* ======================
   BELÄSTIGUNG
   ====================== */
('belaestigung', 'Belästigung',
$$Definition: Unerwünschte, aufdringliche oder störende Handlungen.

Beispiele:
"Er belästigte andere durch ständiges Ansprechen."
"Er bedrängte eine Bedienstete verbal."
$$,
'prompt_belaest_v1'),

/* ======================
   ALKOHOL / DROGEN
   ====================== */
('alkohol_drogen', 'Alkohol/Drogen',
$$Definition: Vorfall mit auffälligem Verhalten oder Gefährdung durch Rauschmittel.

Beispiele:
"Insasse war deutlich alkoholisiert."
"Verdacht auf Drogenkonsum."
$$,
'prompt_alkdro_v1')

ON CONFLICT DO NOTHING;

