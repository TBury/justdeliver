# JustDeliver

**JustDeliver** to starszy brat projektu Hercules [https://github.com/TBury/hercules](https://github.com/TBury/hercules) mający dokładnie te same założenia: jest to system rozliczeń dla wirtualnych firm (grup graczy), którzy grają w grę Euro Truck Simulator 2. Służy on do zliczania ilości przejechanych kilometrów, dodawania nowych tras, sprawdzania aktywności *kierowców* i wiele innych rzeczy mających urealnić rozgrywkę.

![https://i.imgur.com/NohinPF.png](https://i.imgur.com/NohinPF.png)

### Założenia projektu

Projekt JustDeliver był reaktywacją projektu Hercules. Do dnia dzisiejszego ma on swoje grono użytkowników, którzy korzystają z tego systemu. Był on zintegrowany z aplikacją desktopową JustDeliver Desktop napisanej w Electronie (JavaScript), jej kod natomiast nie zachował się na repozytorium. Aplikacja desktopowa na podstawie danych telemetrycznych przekazywanych do pamięci wspólnej odczytywała odpowiednie parametry i wysyłała cyklicznie do systemu, co było przetwarzane przez API.
Sam projekt został przeze mnie najpierw zaprojektowany w aplikacji Figma, uwzględniając zasady UX oraz starając się stworzyć czytelny interfejs użytkownika.

### Stack technologiczny

Cały projekt oparty jest na frameworku **Django**. Do tworzenia cyklicznych zadań (crontab) wykorzystałem **huey**, które codziennie o 1.00 generuje zlecenia na giełdzie zleceń dostępnych do wzięcia. Frontend oparty jest na **SCSS/SASS**, pisany zgodnie z metodologią BEM. Nie doczekał się niestety wersji responsywnej. 
Brakuje w nim również dostępnej w projekcie Hercules integracji z Tesseractem, z racji, iż ta w projekcie działała niestabilnie dla określonych warunków.

### Funkcje projektu
Funkcje projektu są identyczne jak w przypadku projektu Hercules: **dodawanie i rozliczanie tras** oraz **generowanie dyspozycji**. *Szef* firmy sprawdzał poprawność zrzutu ekranu z treścią wpisaną do systemu i zatwierdzał bądź odrzucał trasy, które zostały nadesłane przez *kierowców*. Prócz tego system posiada automatyczną *Giełdę zleceń*, której zlecenia generowane są cyklicznie co 24 godziny.
