import json
from random import randint
from time import time

from hps.servers import SocketServer

HOST = '127.0.0.1'
PORT = 5000

class GameServer(object):
    def __init__(self, input_file=None):
        if input_file is None:
            print('No input given')
            exit(1)

        print('Waiting on port %s for player...' % PORT)
        self.accept_player_connections()

        print('Preparing input data')
        parsed_data = self.input_parsing(input_file)
        self.patients = parsed_data[0]
        self.hospitals = parsed_data[1]
        self.ambulances = parsed_data[2]
        self.total_patients = parsed_data[3]
        self.total_hospitals = parsed_data[4]
        self.total_ambulances = parsed_data[5]

        print('Starting Game with player: ' + str(self.player_name))
        self.play_game()

    def input_parsing(self, input_file):
        ### Create dictionaries of patient, hospital, and ambulances

        patients = {}
        hospitals = {}
        ambulances = {}

        patient_id = 0
        hospital_id = 0
        ambulance_id = 0

        # Parse input txt file
        mode = None  # 0 = patient description, 1 = hostpital ambulance number
        f = open(input_file, 'r')
        for line in f:
            if line == '\n':
                continue
            line = line.strip('\n')
            if line[0] == 'p':
                mode = 0
                continue
            if line[0] == 'h':
                mode = 1
                continue

            # Patient information
            if mode == 0:
                mytuple = tuple(map(int, line.split(',')))
                patients[patient_id] = {'xloc': mytuple[0], 'yloc': mytuple[1], 'rescuetime': mytuple[2]}
                patient_id += 1
            elif mode == 1:
                hospitals[hospital_id] = {'xloc': None, 'yloc': None}
                num_ambulances = int(line)
                ambulances_at_hospital = []
                for amb in range(0, num_ambulances):
                    ambulances[ambulance_id] = {'starting_hospital': hospital_id, 'route': None}
                    ambulances_at_hospital += [ambulance_id]
                    ambulance_id += 1
                hospitals[hospital_id]['ambulances_at_start'] = ambulances_at_hospital
                hospital_id += 1
            else:
                print('Error parsing input file')
                exit(1)

        return (patients, hospitals, ambulances, patient_id, hospital_id, ambulance_id)

    def accept_player_connections(self):
        self.server = SocketServer(HOST, PORT, 1)
        self.server.establish_client_connections()
        self.player_attributes = json.loads(self.server.receive_from_all(size=8192)[0])
        self.player_name = self.player_attributes['name']

    def route_time(self, c_loc, n_loc):
        return abs(n_loc[0] - c_loc[0]) + abs(n_loc[1] - c_loc[1])

    def game_over(self, message, patients_saved, finished=False):
        self.server.send_to_all(
            json.dumps({
                'game_completed': finished,
                'message': message,
                'patients_saved': patients_saved,
                'number_saved': len(patients_saved)
            }))
        exit(1)

    def play_game(self):
        input_data = {'patients': self.patients, 'hospitals': self.hospitals, 'ambulances': self.ambulances}
        print(input_data)
        print('---------')
        self.server.send_to(json.dumps(input_data), 0)
        start = time()
        moves = json.loads(self.server.receive_from_all(size=8192)[0])
        stop = time()

        if (stop-start) > 120:
            m = 'Player ' + str(self.player_name) + ' ran for more than 2 minutes'
            self.game_over(m, [])

        hospital_locations = moves['hospital_loc']
        ambulance_moves = moves['ambulance_moves']
        print(hospital_locations)
        print('------')
        print(ambulance_moves)

        for hos_id in range(0, self.total_hospitals):
            xloc = hospital_locations[str(hos_id)]['xloc']
            yloc = hospital_locations[str(hos_id)]['yloc']

            if xloc < 0 or yloc < 0:
                m = 'Invalid hospital location'
                self.game_over(m, [])

            self.hospitals[hos_id]['xloc'] = xloc
            self.hospitals[hos_id]['yloc'] = yloc

        patients_saved = []
        patients_picked_up = []

        for amb_id in range(0, self.total_ambulances):
            try:
                amb_route = ambulance_moves[str(amb_id)]
            except Exception as e:
                continue
            current_loc = (self.hospitals[self.ambulances[amb_id]['starting_hospital']]['xloc'], self.hospitals[self.ambulances[amb_id]['starting_hospital']]['yloc'])

            time_counter = 0
            p_inside_amb = []

            for amb_stop in amb_route:
                if amb_stop[0].lower() == 'p':
                    if len(p_inside_amb) >= 4:
                        m = 'Cannot pick up more than 4 patients'
                        self.game_over(m, [])
                    try:
                        p_id = int(amb_stop[1:])
                        if p_id >= self.total_patients or p_id < 0:
                            m = 'Invalid patient id'
                            print(p_id)
                            self.game_over(m, [])
                    except Exception as e:
                        m = 'Error reading patient id'
                        self.game_over(m, [])
                    if p_id in patients_picked_up:
                        print('Patient ' + str(patient) + ' has already been picked up')
                    else:
                        p_inside_amb += [p_id]
                        patients_picked_up += [p_id]
                    new_loc = (self.patients[p_id]['xloc'], self.patients[p_id]['yloc'])
                    time_taken = self.route_time(current_loc, new_loc)
                    time_counter += time_taken + 1
                    current_loc = new_loc
                    continue
                elif amb_stop[0].lower() == 'h':
                    try:
                        h_id = int(amb_stop[1:])
                        if h_id >= self.total_hospitals or h_id < 0:
                            m = 'Invalid hospital id'
                            self.game_over(m, [])
                    except Exception as e:
                        m = 'Error reading hospital id'
                        self.game_over(m, [])
                    new_loc = (self.hospitals[h_id]['xloc'], self.hospitals[h_id]['yloc'])
                    time_taken = self.route_time(current_loc, new_loc)
                    time_counter += time_taken + 1
                    current_loc = new_loc
                    for patient in p_inside_amb:
                        if time_counter <= self.patients[patient]['rescuetime']:
                            print('Ambulance ' + str(amb_id) + ' saved patient ' + str(patient))
                            patients_saved += [patient]
                        else:
                            print('Patient ' + str(patient) + ' died before reaching the hospital')

                    p_inside_amb = []
                    continue
                else:
                    m = 'Invalid route stop'
                    self.game_over(m, [])

        print('All ambulances have finished their routes')
        print('Patients saved:')
        print(patients_saved)
        print('Total number of patients saved: ' + str(len(patients_saved)))
        self.game_over('Congratulations!', patients_saved, finished=True)