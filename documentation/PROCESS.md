
![LOGO](./images/dzos_logo.png)

# DZOS: Dynamic Z Offset and Soaking

## PRE-REQUISITES:
1. SV08 3D Printer with an inductive sensor.
2. File transfer software (examples below):
    - [FileZilla](https://filezilla-project.org/)
    - [winSCP](https://winscp.net/)
3. `START_PRINT` using an adaptive bed mesh and input temperature from slicer.

## INSTALL:
1. Access the SV08 filesystem. (`user: sovol` - `password: sovol`)
2. Transfer provided files to their respective folders in `/home/sovol/...`.
3. Restart Klipper service or hard reboot printer.
4. Add `[include dzos.cfg]` to your `printer.cfg`.
5. The `dzos.cfg` overrides your `START_PRINT`.

## CONFIGURATION:
1. If you'd like to adjust your own `START_PRINT`, add the DZOS call: `DZOS_Z_OFFSET TEMP=<INPUT TEMP> SOAK_TIME=<INPUT SECONDS>` just before: `BED_MESH_CALIBRATE ADAPTIVE=1`. Remove the included `START_PRINT` from the provided `dzos.cfg` macro.

## SETUP:
1. The setup process for DZOS only needs to be done when required. If you change your nozzle dimensions or probe you need to re-run the setup.
2. **IMPORTANT:** Wait for your printer to be `cold and at room temperature` for setup.
3. Navigate to the web interface for your printer.
4. Under the MACRO section press: `DZOS Enable`. Once pressed hit `SAVE CONFIG` and wait for your printer to restart.
5. Run the following macro: `DZOS INIT SETUP`.
6. The setup is in the form of a guided 2-part PLA print. Use the web interface or device screen to view the real-time instructions.

    ### Guided print overview:
    - **PREP:** Clean your nozzle of filament. Load PLA.
    - **A:** Printer probe samples at room temperature.
    - **B:** Temperature rises to 65C.
    - **C:** Printer probe samples.
    - **D:** Adaptive bed mesh and then a test print begins.
    - **E:** `BEEP - USER INTERACTION - BEEP:` Adjust z offset to your desired z offset as the print prints.
    - **F:** Automatic capture of user input z offset.
    - **G:** `BEEP - USER INTERACTION - BEEP:` Clean finished print either immediately or during the next step.
    - **H:** 1000 second heat soak at 65C.
    - **I:** Repeat of D -> F.
    - **J:** Setup is finished.

## USAGE:
1. Print as normal. The Z offset will calculate per print.
2. Use a custom `START_PRINT` with temperature input from your slicer. Add to the DZOS call for best results. 
3. Happy testing!

## DISABLE/RE-ENABLE:
1. `DZOS Disable` macro will stop the code from running. No other changes required.
2. `DZOS Enable` macro will re-enable usage. You do not have to re-run the setup.

## UNINSTALL:
1. Remove `/home/sovol/printer_data/config/dzos.cfg`
2. Remove `/home/sovol/printer_data/config/dzos_print_data.json`
3. Remove `/home/sovol/printer_data/config/dzos_static_data.json`
4. Remove `/home/sovol/printer_data/gcodes/dzos_test_combined.gcode`
5. Remove `/home/sovol/klipper/klippy/extras/dzos.py`
6. Ensure your `printer.cfg`'s saved variables related to `[dzos]` are removed.

## ISSUES:
- May not support mainline klipper. Untested.
- May not work properly with pause/resume. Untested.