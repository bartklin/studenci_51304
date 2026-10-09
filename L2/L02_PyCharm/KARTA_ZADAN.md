# Karta zadań — L02
## Cel
Poznasz podział systemu na obsługę danych, logikę biznesową i prezentację. Skorzystasz z gotowych procedur, aby sformułować proste zasady i sprawdzić wynik. Nie piszesz importera CSV/JSON ani klas.

## Plan 135 minut (przerwy osobno)
**Część 1, 45 min:** uruchomienie, rozpoznanie karty, Z1 i Z2. **Część 2, 45 min:** Z3, Z4 i kontrola wybranych zamówień. **Część 3, 45 min:** testy, przypadki graniczne, raport i oddanie. Gdy potrzebujesz wsparcia, użyj POMOC.md zamiast zatrzymywać się na składni.

## Kontrakt danych — czytaj `z.pole`
`z` jest już przygotowaną kartą jednego zamówienia. Nie tworzysz tego obiektu.

| Pole | Znaczenie / przykład |
|---|---|
| `z.id` | Identyfikator, np. `Z003` |
| `z.status` | `nowe`, `w_realizacji`, `zrealizowane`, `anulowane` |
| `z.klient_vip` | Wartość logiczna `True`/`False` |
| `z.blokada_klienta` | Czy klient wymaga weryfikacji |
| `z.dni_po_terminie` | 0 w dniu terminu lub przed nim; dodatnia liczba po terminie |
| `z.wartosc_gr` | Wartość całego zamówienia w groszach |
| `z.wplacono_gr` | Suma wpłat na to zamówienie, w groszach |
| `z.ilosc` | Zamówione sztuki jednego produktu |
| `z.dostepne_szt` | Stan produktu minus wcześniejsze rezerwacje |
| `z.brakuje_szt` | 0 gdy towaru wystarcza, dodatnia liczba gdy brakuje |

Gotowa funkcja **`pozostalo_do_zaplaty(z)`** wyznacza brakującą kwotę. Wystarczy wywołać ją w warunku. Dla Z003: wartość 600000 gr, wpłata 300000 gr, brakuje 300000 gr.

## Z1. Zamówienie otwarte
W `czy_otwarte(z)` zastąp `return None` odpowiednim warunkiem. Zwróć **True** tylko dla statusów `nowe` i `w_realizacji`. Inne dwa statusy są zamknięte w rozumieniu naszego ćwiczenia.

**Sprawdź:** Z001 — otwarte; Z005 — nie; Z006 — nie. Minimum: poprawny jeden warunek, bez pętli. Pomoc: wzorzec operatora `in`.

## Z2. Otwarte i opóźnione
W `czy_opoznione(z)` użyj gotowego już `czy_otwarte(z)` oraz dodatniej liczby dni po terminie. Połącz warunki operatorem **and**.

**Sprawdź:** Z001 — tak; Z011 — nie (termin dzisiaj); Z006 — nie mimo dawnego terminu (zrealizowane). W tym ćwiczeniu badamy bieżące otwarte zaległości, a nie historyczną terminowość wszystkich dostaw.

## Z3. Priorytet
Najpierw zapisz wynik słownie. Następnie użyj dwóch `if` i końcowego `return`.

| Warunek | Wynik |
|---|---|
| Zamówienie nie jest opóźnione według Z2 | `STANDARD` |
| Jest opóźnione i klient VIP | `PILNE` |
| Pozostałe opóźnione | `WYSOKI` |

**Sprawdź:** Z001 — PILNE; Z002 — WYSOKI; Z011 — STANDARD. Sama cecha VIP nie wystarcza do PILNE. Priorytet nie jest zgodą na wydanie towaru.

## Z4. Decyzja — pierwsza pasująca zasada
Uzupełnij `decyzja(z)`. Zachowaj poniższą kolejność. Nie zmieniaj wielkich liter w wynikach. Każda karta ma dostać dokładnie jeden wynik, nie listę wszystkich przeszkód.

| Kolejność | Jeżeli… | Zwróć |
|---:|---|---|
| 1 | status = `anulowane` | `POMIN_ANULOWANE` |
| 2 | status = `zrealizowane` | `ZAKONCZONE` |
| 3 | `z.blokada_klienta` jest True | `WERYFIKACJA` |
| 4 | `pozostalo_do_zaplaty(z)` jest większe od 0 | `UZUPELNIJ_PLATNOSC` |
| 5 | `z.brakuje_szt` jest większe od 0 | `UZUPELNIJ_MAGAZYN` |
| 6 | żaden wcześniejszy warunek nie pasuje | `GOTOWE` |

**Sprawdź cztery karty:** Z004 (weryfikacja), Z003 (dopłata), Z007 (magazyn), Z001 (gotowe). Z005 ma pozostać anulowane, a nie zostać wezwane do zapłaty.

**Ograniczenie:** kwalifikacja nie zmienia zapasu i nie jest rezerwacją. Z001 oraz Z002 osobno mogą być GOTOWE, choć łącznie wymagają 6 monitorów przy 5 wolnych. Zasady są dydaktyczne — nie opisują uniwersalnej polityki kredytowej lub księgowej.

## Kontrola i wniosek
Uruchom `testy_regul.py`. Przed poprawianiem zapisz oczekiwanie dla: terminu dzisiaj, zapasu równego ilości, wpłaty równej wartości i anulowania połączonego z brakiem pieniędzy. Nie zmieniaj źródeł ani testu tylko po to, by uzyskać zielony wynik.

Wynik referencyjny omawiany na zajęciach: **12 poprawnych → 10 otwartych → 7 opóźnionych otwartych**. Najpierw uzgodnij konkretne karty, potem sumy. Trzy odrzucone rekordy są jawnie pokazane w kwarantannie i nie należą do tych 12.

Wypełnij kartę pracy. Dwa zdania podsumowania: co wynika z danych i czego nie da się jeszcze stwierdzić.

## Rozszerzenie (nieobowiązkowe)
Po uzupełnieniu i sprawdzeniu zasad uruchom `rozszerzenie_przydzial.py`. Gotowa procedura pracuje na kopii magazynu, kolejności ID i całych zamówieniach. Porównaj liczbę kandydatów z liczbą przydziałów. Nie jest to optymalizacja ani zapis do źródła. Alternatywa dla osób utrwalających podstawy: opisz dwa dodatkowe przypadki testowe swojej reguły.
