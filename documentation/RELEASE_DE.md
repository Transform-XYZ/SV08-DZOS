![LOGO](./images/dzos_logo.png)

# DZOS: Dynamischer Z-Versatz und Temperatur-Soaking

## VORAUSSETZUNGEN:
1. SV08 3D-Drucker mit einem induktiven Sensor.
2. Software für Dateiübertragungen (Beispiele unten):
    - [FileZilla](https://filezilla-project.org/)
    - [winSCP](https://winscp.net/)
3. Konfiguriere deinen Slicer so, dass `TEMP=<TEMP FROM SLICER>` an `START_PRINT` übergeben wird.

## INSTALLATION:
1. Auf das Dateisystem des SV08 zugreifen (`Benutzer: sovol` – `Passwort: sovol`).
2. Ordner nach `/home/sovol/...` übertragen und vorhandene Dateien überschreiben.
3. Klipper-Dienst neu starten oder den Drucker vollständig neu starten.
4. `printer.cfg` bearbeiten:
    - Füge `[include dzos.cfg]` in `printer.cfg` nach den anderen `[include]`-Zeilen ein.
5. Änderungen in `printer.cfg` speichern und Drucker neu starten.

## KONFIGURATION (OPTIONAL):
1. Die `dzos.cfg` überschreibt dein `START_PRINT`. Dies ist standardmäßig aktiviert, aber optional.
2. Falls du dein eigenes `START_PRINT` anpassen möchtest, beachte Folgendes:
    - Stelle sicher, dass du das adaptive Bett-Mesh verwendest.
    - Füge den DZOS-Befehl `_DZOS_PRINT TEMP=<INPUT TEMP>` direkt vor `BED_MESH_CALIBRATE_BASE ADAPTIVE=1` hinzu.
    - Stelle sicher, dass dein Slicer die Temperatur korrekt an `START_PRINT` übergibt.
    - Entferne das mitgelieferte `START_PRINT`-Makro aus `dzos.cfg`.

## EINRICHTUNG:
1. Die DZOS-Einrichtung ist nur erforderlich, wenn du deine Düsengröße oder den Sensor änderst.
2. WICHTIG: Der Drucker muss **kalt und auf Raumtemperatur** sein.
3. Werkzeugkopf-Abdeckung entfernen, um bessere Sicht zu haben.
4. Web-Oberfläche des Druckers aufrufen.
5. Im Makro-Menü auf `DZOS Enable` klicken, dann `SAVE CONFIG` drücken und warten, bis der Drucker neu startet.
6. Danach `DZOS INIT SETUP` auswählen.
7. Die Einrichtung erfolgt in einem geführten 2-stufigen PLA-Druckprozess. Die Web-Oberfläche oder das Drucker-Display zeigt Echtzeit-Anweisungen an.

    ### Übersicht des geführten Drucks:
    - **VORBEREITUNG:** Düse von Filamentrückständen reinigen, PLA laden.
    - **A:** Der Sensor misst bei Raumtemperatur.
    - **B:** Die Temperatur steigt auf 65 °C.
    - **C:** Der Sensor misst erneut.
    - **D:** Adaptive Bett-Mesh-Kalibrierung und Start eines Testdrucks.
    - **E:** `BEEP - NUTZEREINGABE ERFORDERLICH - BEEP`: Während des Drucks den Z-Versatz manuell nachjustieren.
    - **F:** Automatische Speicherung des eingestellten Z-Versatzes.
    - **G:** `BEEP - NUTZEREINGABE ERFORDERLICH - BEEP`: Gedrucktes Teil entfernen (sofort oder später).
    - **H:** 1000 Sekunden Wärme-Soaking bei 65 °C.
    - **I:** Wiederholung von C → F.
    - **J:** Einrichtung abgeschlossen. Der Drucker startet neu.

## VERWENDUNG:
1. Die Wärmeeinwirkzeit vor dem Druck in der Web-Oberfläche mit `DZOS SOAK TIME` einstellen.
    - **RICHTWERTE:** Werte für einen kalten Drucker, spätere Drucke benötigen 0 Sekunden.
    - **KLEIN:** 0
    - **MITTEL/GROß:** 500–1000
    - **GESAMTES BETT:** ~1500
2. Druck wie gewohnt starten. Der Z-Versatz wird automatisch pro Druck berechnet.
3. Viel Erfolg beim Drucken!

## DEAKTIVIEREN / REAKTIVIEREN:
1. `DZOS Disable`-Makro deaktiviert DZOS – keine weiteren Änderungen nötig.
2. `DZOS Enable`-Makro aktiviert DZOS erneut, ohne dass die Einrichtung wiederholt werden muss.

## DEINSTALLATION:
1. Entferne folgende Dateien:
    - `/home/sovol/printer_data/config/dzos.cfg`
    - `/home/sovol/printer_data/config/dzos_print_data.json`
    - `/home/sovol/printer_data/config/dzos_static_data.json`
    - `/home/sovol/printer_data/gcodes/dzos_test_*.gcode`
    - `/home/sovol/klipper/klippy/extras/dzos.py`
2. Entferne alle `[dzos]`-bezogenen Variablen in `printer.cfg`.

## BEKANNTE PROBLEME:
- Pause/Wiederaufnahme (Pause/Resume) wurde nicht getestet und könnte Probleme verursachen.
