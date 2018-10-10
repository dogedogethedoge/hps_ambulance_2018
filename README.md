# hps_ambulance_2018

This is the architecture for the ambulance problem.

## The Game
The ambulance game is non-adversarial, meaning you are not playing against an opponent. Each team will have two minutes to determine optimal placement of hospitals and ambulance routes. The server will send the client all of the data it needs to determine this and then the client will respond with its solution.

The game will have 300 patients on a 1001 x 1001 grid (0 <= x,y <= 1000) and 5 hospitals with some number of ambulances starting at each hospital. No hospital will start with more than 25 ambulances.

Patients are considered saved if they reach the hospital with at least 1 minute left remaining (to account for the 1 minute to unload the patient).

You may place hospitals anywhere on the grid, including on top of each other and on top of patients. If the hospital is on top of a patient, they are not automatically rescued. They must still be picked up by an ambulance and dropped off (so minimum of 2 minutes).

Patients may be at the same location. In such a case, each patient still takes 1 minute to load (as per the rules on the website).

Rules that must be followed. Failure to follow these rules will result in a forfeit of the game:
* An ambulance can pick up no more than 4 patients at a time. Any ambulance route attempting to pick up more than 4 patients will forfeit the game.
    * Dead patients still count. Their bodies must be dropped off at the hospital before their spot on the ambulance is freed.
* A patient may only be picked up once. If any ambulance attempts to pick up a patient already picked up by another ambulance, they will not pick up that patient and will not incur the 1 minute penalty of loading a patient into the ambulance.
* Ambulance routes are validated in order of their id, so if two ambulances attempt to pick up the same patient, the ambulance with the smaller id will be the one to take the patient.
* All hospitals must be assigned a location. Failure to do so will forfeit the game.

## Setup Client / Server Code

1. This project uses `python3.6`. If you haven't already, please install it.
2. Download dependencies: The only dependency that doesn't come standard is hps-nyu
    `pip install hps-nyu==1.0.0` 

## Running the Code

The run_game.py file can run either the server or the client. The terminal command looks like:
```
python run_game.py [-t] {s/c} [-i] {input file} [-n] {player name}
```

* `-t` is required and indicates whether this instance of run_game.py is running the server or the client. `-t s` runs the server, `-t c` runs the client.
* `-i` is required if this instance is running the server and takes in the path to the input text file
* `-n` is entirely optional. It is unused for the server instance. If running the client instance, you can input a custom name for the player. The default name is `Default_Player`

To run the game in full, open two instances of your choice of terminal and cd into the appropriate directory. Launch the server FIRST, then launch the client.

Example:
1. In terminal 1 enter `python -t s -i test_300.txt`
2. In terminal 2 enter `python -t c -n My_Name`

The results of the game should appear on both terminals.

Example:
```
Congratulations!
Patients that lived:
[]
---------------
Number of patients saved = 0
```

##### NOTE: If you wish to rename your client file to something other than 'client.py', please remember to update the import line in      run_game.py to 'from <your_client_name> import Player'

## Including Your Client Code

The players only need to modify one file: client.py

Inside client.py you will find several functions but the only one that players need modify is the `your_algorithm(self)` function. Included in the code is a dumb test algorithm that fails to save anyone. This can be entirely scrapped and replaced with your code.
The function itself has a docstring detailing the available data and the format of the output, which is copied below:
```
You have access to the dictionaries 'patients', 'hospitals', and 'ambulances'
These dictionaries are structured as follows:
    patients[patient_id] = {'xloc': x, 'yloc': y, 'rescuetime': rescuetime}

    hospitals[hospital_id] = {'xloc': None, 'yloc': None, 'ambulances_at_start': [array of ambulance_ids]}

    ambulances[ambulance_id] = {'starting_hospital': hospital_id}

RETURN INFO
-----------
You must return a tuple of dictionaries (hospital_locations, ambulance_routes). These MUST be structured as:
    hospital_locations[hospital_id] = {'xloc': x, 'yloc': y}
        These values indicate where you want the hospital with hospital_id to start on the grid

    ambulance_routes[ambulance_id] = {[array of stops along route]}
        This array follows the following rules:
            - The starting location of each ambulance is known so array must start with first patient that
              it must pick up (or hospital location that it will head to)
            - There can only ever be up to 4 patients in an ambulance at a time so any more than 4
              patient stops in a row will result in an invalid input
            - A stop for a patient is a string starting with 'p' followed by the id of the patient i.e. 'p32'
                + The 'p' can be uppercase or lowercase
                + There can be no whitespace, i.e. 'p 32' will not be accepted
            - A stop for a hospital is the same as the patient except with an 'h', i.e. 'h3'
                + The 'h' can also be uppercase or lowercase

    Example:
        ambulance_routes[3] = ['p0', 'p43', 'h4', 'p102', 'p145', 'p241', 'p32', 'h1']

        This will be read as ambulance #3 starts at it's designated hospital, goes to patient #0, then to
        patient #43, then drops both off at hospital #4, then picks up patients #102, #145, #241, #32 in that
        order then drops all of them off at hospital #1
```

## Code in Another Language

If you wish to use a language other than python, I leave the implementation of the client to you. However the client must follow the following rules:
* The client must send and receive very specific messages:
  1. The client connects to the server
  2. The client sends a message to the server: `{'name': player_name}`
  3. The client waits for a message from the server: `{'buffer_size': size_of_buffer}`
      * This message contains the buffer size needed to receive the next message
  4. The client waits for a message from the server: 
        ```{'patients': dict_of_patients, 'hospitals': dict_of_hospitals, 'ambulances': dict_of_ambulances}```
  5. The client computes its response via provided algorithm
  6. The client sends a message to the server: `{'buffer_size': size_of_buffer}`
      * This message contains the buffer size needed to receive the next message
  7. The client sends a message to the server: `{'hospital_loc': hos_locations, 'ambulance_moves': amb_routes}`
* The client responses must match the format given above, with the values `hos_locations` and `amb_routes` matching the format given in the previous section
