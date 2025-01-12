######################################################################################################################################################################################################
# DZOS: DYNAMIC Z OFFSET AND SOAK
# AUTHOR: TRANSFORM
# DATE: 2025-01-12
# VERSION: 0.1.36
######################################################################################################################################################################################################
import json
import os
import numpy as np
######################################################################################################################################################################################################
# PATHS
######################################################################################################################################################################################################
static_filepath = "/home/sovol/printer_data/config/dzos_static_data.json"
print_data_filepath = "/home/sovol/printer_data/config/dzos_print_data.json"
######################################################################################################################################################################################################

print()

class DZOS:
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()
        self.config_name = config.get_name()
    
        self.speed = self.config.getfloat('speed', default=300)
        self.hop_z = self.config.getfloat("z_hop", default=7.5)
        self.speed_z_hop = self.config.getfloat('speed_z_hop', default=10)
        self.dzos_enabled = self.config.getint('enabled', default=0)
        self.dzos_calculated = self.config.getint('calculated', default=0)

        probe_config = self.config.getsection('probe')
        probe_offset_x = probe_config.getfloat('x_offset')
        probe_offset_y = probe_config.getfloat('y_offset')
        self.probe_offset_z = probe_config.getfloat('z_offset')
        
        self.bed_xy = list(self.config.getfloatlist("bed_xy", count=2, default=[191, 165]))
        self.pressure_nozzle_xy = list(self.config.getfloatlist("pressure_xy", count=2, default=[289, 361]))
        self.pressure_xy = [self.pressure_nozzle_xy[0] - probe_offset_x, self.pressure_nozzle_xy[1] - probe_offset_y]

        self.gcode = self.printer.lookup_object('gcode')
        self.gcode_move = self.printer.lookup_object('gcode_move')

        self.gcode.register_command("DZOS_Z_OFFSET", self.cmd_DZOS_Z_OFFSET)
        self.gcode.register_command("DZOS_Z_CALCULATE", self.cmd_DZOS_Z_CALCULATE)
        self.gcode.register_command("DZOS_Z_CAPTURE", self.cmd_DZOS_Z_CAPTURE)


    def cmd_DZOS_Z_OFFSET(self, gcmd):
        self._init_printer_objects()
        cache_static = int(gcmd.get("CACHE_STATIC", 0))
        soak_time = int(gcmd.get("SOAK_TIME", 0))
        calibration_temp = int(gcmd.get("TEMP", 0))        
        enable = int(gcmd.get("ENABLE", -1))
        test_name = gcmd.get("TEST", None)
        if enable == 1:
            self.global_configfile.set(self.config_name, "enabled", 1)
            gcmd.respond_info("DZOS: Now Enabled!")
            self._display_msg("DZOS: Enabled!")
            return
        elif enable == 0:
            self.global_configfile.set(self.config_name, "enabled", 0)
            gcmd.respond_info("DZOS: Now Disabled!")
            self._display_msg("DZOS: Disabled!")
            return
        if not self.dzos_enabled:
            gcmd.respond_info("DZOS: Disabled!")
            self._display_msg("DZOS: Disabled!")
            return
        if cache_static == 1:
            self._cache_static(gcmd)
            return
        if calibration_temp > 0:
            self._set_temperature(calibration_temp, blocking=True)        
        if test_name:
            self._calculate_static_data(gcmd, test_name, soak_time)
            return            
        if not os.path.exists(static_filepath) or self.pressure_xy == [0,0] or self.dzos_calculated == 0:
            gcmd.respond_info("DZOS: No Static Data Found!")
            self._display_msg("DZOS: No Static!")
            return
        self._calculate_dynamic_offset(gcmd, soak_time)


    def cmd_DZOS_Z_CALCULATE(self, gcmd):
        self._init_printer_objects()
        static_data = read_data(static_filepath)

        offset_factor, adjustment_factor = optimize_factors(static_data['offset_pressure_rt'], 
                                                            static_data['offset_pressure_at'], 
                                                            static_data['z_offset_rt'], 
                                                            static_data['z_offset_at'])
        static_data = read_data(static_filepath)
        static_data["offset_factor"] = offset_factor
        static_data["adjustment_factor"] = adjustment_factor
        write_data(static_filepath, static_data)
        self.global_configfile.set(self.config_name, "calculated", 1)
        gcmd.respond_info("DZOS: Stored..")
        self._display_msg("DZOS: Stored..")



    def cmd_DZOS_Z_CAPTURE(self, gcmd):
        self._init_printer_objects()
        capture_name = str(gcmd.get("NAME", None))
        toolhead = self.printer.lookup_object('toolhead')
        z_position = toolhead.get_position()[2]
        z_offset = 10.0 - z_position
        if capture_name.lower():
            static_data = read_data(static_filepath)
            static_data[f"z_offset_{capture_name.lower()}"] = z_offset
            write_data(static_filepath, static_data)
        else:
            gcmd.respond_info("DZOS: Fail!")
            self._display_msg("DZOS: Fail!")


    def _init_printer_objects(self):
        self.toolhead = self.printer.lookup_object('toolhead')
        self.probe_object = self.printer.lookup_object('probe')
        self.probe_pressure_object = self.printer.lookup_object('probe_pressure')
        self.display_status_object = self.printer.lookup_object('display_status')
        self.global_configfile = self.printer.lookup_object('configfile')
        self.heater_bed = self.printer.lookup_object('heater_bed')


    def _init_static_data(self):
        static_data = read_data(static_filepath)
        self.static_b_pressure_z = static_data["b_pressure_z"]
        self.static_e_bed_z = static_data["e_bed_z"]
        self.static_e_pressure_nozzle = static_data["e_pressure_nozzle_z"]
        self.static_offset_factor = static_data["offset_factor"]
        self._static_adjustment_factor = static_data["adjustment_factor"]


    def _calculate_static_data(self, gcmd, test_name, soak_time):
        self._heat_soak(duration=soak_time)
        self._display_msg("DZOS: Test..")
        self._generic_z_probe(gcmd, self.probe_object, x=self.bed_xy[0], y=self.bed_xy[1], zero=True)
      
        d_pressure_z_s1 = self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1])
        d_pressure_z_s2 = self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1])
        d_pressure_z = (d_pressure_z_s1 + d_pressure_z_s2) / 2
        self._set_z_zero(d_pressure_z)

        static_data = read_data(static_filepath)
        static_b_pressure_z = static_data["b_pressure_z"]
        static_e_pressure_nozzle = static_data["e_pressure_nozzle_z"]

        offset_pressure = (d_pressure_z - static_b_pressure_z)
        static_data[f"offset_pressure_{test_name.lower()}"] = offset_pressure
        write_data(static_filepath, static_data)
        self._set_z_offset(static_e_pressure_nozzle + self.probe_offset_z)


    def _cache_static(self, gcmd):
        self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1], zero=True)
        
        e_pressure_nozzle = self._generic_z_probe(gcmd, self.probe_pressure_object, x=self.pressure_nozzle_xy[0], y=self.pressure_nozzle_xy[1])
        e_bed_z_s1 = self._generic_z_probe(gcmd, self.probe_object, x=self.bed_xy[0], y=self.bed_xy[1])
        e_bed_z_s2 = self._generic_z_probe(gcmd, self.probe_object, x=self.bed_xy[0], y=self.bed_xy[1])
        e_bed_z = (e_bed_z_s1 + e_bed_z_s2) / 2
        self._set_z_zero(e_bed_z)

        b_pressure_z_s1 = self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1])
        b_pressure_z_s2 = self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1])
        b_pressure_z = (b_pressure_z_s1 + b_pressure_z_s2) / 2
        self._set_z_zero(b_pressure_z)
        data_dict = {
            "b_pressure_z": b_pressure_z,       
            "e_bed_z": e_bed_z,
            "e_pressure_nozzle_z": e_pressure_nozzle
        }
        write_data(static_filepath, data_dict)


    def _calculate_dynamic_offset(self, gcmd, soak_time):
        self._heat_soak(duration=soak_time)
        self._display_msg("DZOS: Calc..")
        
        d_bed_z_s1 = self._generic_z_probe(gcmd, self.probe_object, x=self.bed_xy[0], y=self.bed_xy[1])
        d_bed_z_s2 = self._generic_z_probe(gcmd, self.probe_object, x=self.bed_xy[0], y=self.bed_xy[1])
        d_bed_z = (d_bed_z_s1 + d_bed_z_s2) / 2
        self._set_z_zero(d_bed_z)

        d_pressure_z_s1 = self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1])
        d_pressure_z_s2 = self._generic_z_probe(gcmd, self.probe_object, x=self.pressure_xy[0], y=self.pressure_xy[1])
        d_pressure_z = (d_pressure_z_s1 + d_pressure_z_s2) / 2
        self._set_z_zero(d_pressure_z)
            
        z_offset = self._calculate_z_offset(d_pressure_z)
        print_data = self._create_data_dict(d_bed_z, d_pressure_z, -z_offset)
        append_data(print_data_filepath, print_data)

        gcmd.respond_info("DZOS: Z Offset: %.3f" % z_offset)
        self._display_msg(f"DZOS: {z_offset:.3f}")
        
        self._set_z_offset(z_offset + self.probe_offset_z)


    def _heat_soak(self, duration):
        iteration = 0
        while iteration < duration:
            self._display_msg(f"DZOS: Soak-{int(duration - iteration)}s")
            self.toolhead.dwell(1)
            iteration += 1


    def _display_msg(self, msg):
        gcmd = self.gcode.create_gcode_command(f"M117 {msg}", f"M117 {msg}", {})
        self.display_status_object.cmd_M117(gcmd)


    def _calculate_z_offset(self, d_pressure_z):
        self._init_static_data()
        offset_pressure = (d_pressure_z - self.static_b_pressure_z)
        target_z_offset = (self.static_offset_factor * offset_pressure) + self._static_adjustment_factor
        return -target_z_offset


    def _generic_z_probe(self, gcmd, probe_object, x, y, zero=False, hop=True):
        version = str(self.printer.start_args['software_version'])
        if version.startswith('v0.12.0-0-g'):
            return self._stock_z_probe(gcmd, probe_object, x, y, zero, hop)
        else:
            return self._latest_z_probe(gcmd, probe_object, x, y, zero, hop)


    def _stock_z_probe(self, gcmd, probe_object, x, y, zero=False, hop=True):
        if hop:
            self._execute_hop_z(self.hop_z)
            self.toolhead.manual_move([x, y, None], self.speed)
        probe_z = probe_object.run_probe(gcmd)[2]
        if zero:
            current = list(self.toolhead.get_position())
            current[2] = current[2] - probe_z
            self.toolhead.set_position(current)
        return probe_z


    def _latest_z_probe(self, gcmd, probe_object, x, y, zero=False, hop=True):
        if hop:
            self._execute_hop_z(self.hop_z)
            self.toolhead.manual_move([x, y, None], self.speed)
        probe_session = probe_object.start_probe_session(gcmd)
        probe_session.run_probe()
        probe_z = probe_session.pull_probed_results()[0][2]
        probe_session.end_probe_session()
        if zero:
            current = list(self.toolhead.get_position())
            current[2] = current[2] - probe_z
            self.toolhead.set_position(current)
        return probe_z


    def _move_z_zero(self, gcmd, probe_object, x, y):
        probe_static_z = self._generic_z_probe(self.toolhead, gcmd, probe_object, x, y)
        current = list(self.toolhead.get_position())
        current[2] = current[2] - probe_static_z
        self.toolhead.set_position(current)

    def _set_z_zero(self, z):
        current = list(self.toolhead.get_position())
        current[2] = current[2] - z
        self.toolhead.set_position(current)

    def _execute_hop_z(self, z):
        self.toolhead.manual_move([None, None, z], self.speed_z_hop)

    def _set_z_offset(self, offset):
        gcmd_offset = self.gcode.create_gcode_command("SET_GCODE_OFFSET", "SET_GCODE_OFFSET", {'Z': offset})
        self.gcode_move.cmd_SET_GCODE_OFFSET(gcmd_offset)

    def _save_z_offset(self):
        gcmd_probe_save = self.gcode.create_gcode_command("Z_OFFSET_APPLY_PROBE", "", {})
        self.printer.lookup_object('probe').cmd_Z_OFFSET_APPLY_PROBE(gcmd_probe_save)

    def _create_data_dict(self, d_bed_z, d_pressure_z, z_offset=None):
        self._init_static_data()
        data_dict = {
            "b_pressure_z": self.static_b_pressure_z,
            "e_bed_z": self.static_e_bed_z,
            "e_pressure_nozzle_z": self.static_e_pressure_nozzle,
            "d_bed_z": d_bed_z,
            "d_pressure_z": d_pressure_z,
        }
        if z_offset:
            data_dict["d_offset_z"] = z_offset
        return data_dict

    def _set_temperature(self, temperature, blocking=False):
        gcode_string = "M140"
        if blocking:
            gcode_string = "M190"
        gcmd_heater_set = self.gcode.create_gcode_command(
            gcode_string,
            gcode_string,
            {
                "S": temperature,
            }
        )
        if blocking:
            self.heater_bed.cmd_M190(gcmd_heater_set)
        else:
            self.heater_bed.cmd_M140(gcmd_heater_set)


def load_config(config):
    return DZOS(config)




######################################################################################################################################################################################################
# UTILS
######################################################################################################################################################################################################


def write_data(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def append_data(file_path, data):
    if not os.path.exists(file_path):
        write_data(file_path, [])
    loaded_data: list = read_data(file_path)
    loaded_data.append(data)
    with open(file_path, "w") as file:
        json.dump(loaded_data, file, indent=4)


def read_data(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


######################################################################################################################################################################################################
# SCIPY.OPTIMIZE IN NUMPY (CHATGPT)
######################################################################################################################################################################################################



def optimize_factors(pressure_offset_rt, presure_offset_at, z_offset_rt, z_offset_at):
    learning_rate = 0.1
    epochs = 10000
    tolerance = 1e-8
    factors = np.array([1.0, 0.0])
    dataset = np.array([
        [
            pressure_offset_rt,
            z_offset_rt,
        ],
        [
            presure_offset_at,
            z_offset_at,
        ]
    ])
    n = dataset.shape[0]
    previous_error = float('inf')
    for index in range(epochs):
        offset_pressure = dataset[:, 0]
        target_z_offset = dataset[:, 1]

        predicted_z_offset = calculate_target(factors[0], offset_pressure, factors[1])

        error_diff = predicted_z_offset - target_z_offset
        gradient = np.array([
            np.sum(error_diff * offset_pressure) / n,
            np.sum(error_diff) / n
        ])
        factors -= learning_rate * gradient
        current_error = calculate_error(factors, dataset)
        if abs(previous_error - current_error) < tolerance:
            break
        previous_error = current_error
    offset_factor = factors[0]
    adjustment_factor = factors[1]
    return offset_factor, adjustment_factor



def calculate_error(factors, dataset):
    offset_factor, adjustment_factor = factors
    offset_pressure = dataset[:, 0]
    target_z_offset = dataset[:, 1]

    predicted_z_offset = calculate_target(offset_factor, offset_pressure, adjustment_factor)
    errors = (predicted_z_offset - target_z_offset) ** 2
    return np.mean(errors)



def calculate_target(offset_factor, offset_pressure, adjustment_factor):
    return (offset_factor * offset_pressure +
            adjustment_factor)