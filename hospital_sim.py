from random import random
import numpy as np
import math

class Patient():
    """
      Object used to represent a patient. Each patient gets assigned differentiating attributes
      such as their arrival type, their triage status (1-5), and to a location in the ED.
    """
    def __init__(self, arrival_type=None, triage_type = None, zone=None, complaint=None):
        self.arrival_type = arrival_type
        self.triage_type = triage_type
        self.zone = zone
        self.complaint = complaint
    
    def assign_patient_arrival_type(self, arrival_type):
        types = {
            0: "ambulance", 
            1: "walk-in"
        }
        self.arrival_type = types[arrival_type]

    def assign_triage_type(self, triage_type):
        self.triage_type = triage_type
        if triage_type in {1,2,4}:
            r = random()
            if r <= 0.5:
                self.complaint = 1 # 1 - Trauma, 2 - Stoke, 4 - Laceration
            else:
                self.complaint = 2 # 1 - Cardiac, 2 - Severe Asthma, 4 - Mild Asthma
        else:
            self.complaint = 1 # 3 - Broken Limb, 5 - Common Cold

    def assign_bed_in_zone(self, zone):
        self.zone = zone
    
class Event():
    """
      Object to represent an event in the simulation. Events can be subclassed into 
      specific kinds of events. Each event contains attributes for time of occurrence
      and associated patient.
    """
    def __init__(self, type=None, patient=None, time=None):
        self.type = type
        self.patient = patient
        self.time = time
    
    def set_type(self, type):
        self.type = type

    def set_patient(self, patient: Patient):
        self.patient = patient
    
    def set_event_time(self, time):
        self.time = time

    def __str__(self):
       types = {
           0: "Ambulance Hospital Arrival",
           1: "Walk-in Arrival",
           3: "Ambulance Hospital Departure",
           4: "Departure from Triage",
           5: "Departure from Initial Workup",
           6: "Departure from Specialist Assessment",
       }
       return f"Event Type: {types[self.type]}"   
         
class AmbulanceHospitalArrivalEvent(Event):
    def __init__(self, time=None, patient=None, diverted_ambulance=False):
        super().__init__(type=1, patient=patient, time=time)
        self.diverted_ambulance = diverted_ambulance
    
    def divert_ambulance(self):
        self.diverted_ambulance = True

class WalkInArrivalEvent(Event):
    def __init__(self, time=None, patient=None):
        super().__init__(type=0, patient=patient, time=time)  

class DepartureAmbulanceEvent(Event):
    def __init__(self, time=None, patient=None):
        super().__init__(type=3, patient=patient, time=time)    

class DepartureTriageEvent(Event):
    def __init__(self, patient=None, time=None):
        super().__init__(type=4, patient=patient, time=time)

class DepartureWorkupEvent(Event):
    def __init__(self, patient=None, time=None):
        super().__init__(type=5, patient=patient, time=time)

class DepartureSpecialistEvent(Event):
    def __init__(self, patient=None, time=None):
        super().__init__(type=6, patient=patient, time=time)

class EndSimulationEvent(Event):
    def __init__(self, time=None):
        super().__init__(type="End Simulation", time=time)

def generate_interarrival_time(clock, arrival_type):
      """
      Generates interarrival time using lambda value of number of patients / hour. 
      """
      r = random()
      a = 0
      hours = clock % (24 * 60) / 60

      if ((hours >= 0 and hours <= 7) or hours == 23):
          a = 6 if arrival_type == 1 else 14
      elif (hours >= 7 and hours <= 11):
          a = 9 if arrival_type == 1 else 10
      elif (hours >= 12 and hours <= 17):
          a = 15 if arrival_type == 1 else 10
      else:
          a = 18 if arrival_type == 1 else 12
      
      return (math.log(1 - r)/(a/60)) * -1

def generate_triage_time(patient):
   """
   Generates service time for triage assessment (only for walk-in patients)
   """
   if (patient.triage_type == 3):
      return np.random.uniform(0.75, 2.25) # More urgent triaging for type 3
   return np.random.uniform(7.5, 11.25)
   
def generate_workup_service_time(patient):
   """
   Generates workup service time for patients of different triage types and 
   associated chief complaints.
   """
   if (patient.triage_type == 1):
       if (patient.complaint == 1):
           return np.random.uniform(5, 12)
       else:
           return np.random.uniform(2, 5)
   elif (patient.triage_type == 2):
       if (patient.complaint == 1):
             return np.random.uniform(5, 15)
       else:
           return 2
   elif (patient.triage_type == 3):
       return np.random.uniform(5, 10)
   elif (patient.triage_type == 4):
       return 2
   else:
       return np.random.uniform(5, 10)

def generate_procedure_time(patient):
   """
   Generates service time for specialist assessment based on their triage type
   and associated chief complaint.
   """
   procedure_times = {
       1 : np.random.uniform(3, 5), # X-ray
       2: np.random.triangular(10, 25, 50, 1)[0], # Surgery Type A
       3: np.random.triangular(30, 45, 90, 1)[0], # Surgery Type B
       4: np.random.uniform(7, 10), # ECG
       5: np.random.uniform(10, 25), # CT Scan
       6: np.random.uniform(2, 5), # Medication
       7: np.random.uniform(5, 10), # Oxygen Therapy
       8: np.random.uniform(2, 3), # Nebulizer
       9: np.random.uniform(5, 15), # Cast/Splint
       10: np.random.triangular(10, 15, 25, 1)[0], # Stitches
       11: np.random.uniform(2, 5), # Tetanus Shot
   }

   total_time = 0
   r1 = random()
   r2 = random()

   if (patient.triage_type == 1):
       if (patient.complaint == 1):
           if r1 <= 0.9:
               total_time += procedure_times.get(1)
           if r2 <= 0.8:
               total_time += procedure_times.get(2)
       else:
            if r1 <= 0.95:
                total_time += procedure_times.get(4)
            if r2 <= 0.6:
                total_time += procedure_times.get(3)
   elif (patient.triage_type == 2):
       if (patient.complaint == 1):
           if r1 <= 0.9:
               total_time += procedure_times.get(5)
           if r2 <= 0.8:
               total_time += procedure_times.get(6)
       else:
           if r1 <= 0.9:
               total_time += procedure_times.get(7)
           if r2 <= 0.7:
               total_time += procedure_times.get(8)
   elif (patient.triage_type == 3):
       if r1 <= 0.8:
           total_time += procedure_times.get(1)
       if r2 <= 0.7:
           total_time += procedure_times.get(9)
   elif (patient.triage_type == 4):
       if (patient.complaint == 1):
            if r1 <= 0.75:
               total_time += procedure_times.get(10)
            if r2 <= 0.3:
               total_time += procedure_times.get(11)
       else: 
            if r1 <= 0.6:
               total_time += procedure_times.get(8)
            if r2 <= 0.3:
               total_time += procedure_times.get(7)
   else:
       if r1 <= 0.9:
           total_time += procedure_times.get(6)
   return total_time

def generate_ambulance_arrival_triage_type():
   """
   Assigns triage type for ambulance patients (limited to types 1,2,3,4)
   """
   triage_type = None
   r = random()
   if r <= 0.2:
      triage_type = 1
   elif r <= 0.55:
      triage_type = 2
   elif r <= 85:
      triage_type = 3
   else:
      triage_type = 4
   return triage_type

def generate_walk_in_triage_type():
   """
   Assigns triage type for walk-in patients (limited to types 3,4,5)
   """
   r = random()
   triage_type = 0
   if r <= 0.33333:
         triage_type = 3
   elif r <= 0.66667:
         triage_type = 4
   else:
         triage_type = 5  
   return triage_type

def emergency_department_simulation(simulation_time):
   global clock
   global fel
   global max_num_servers
   global status_triage_nurses
   global status_workup_doctors
   global status_specialists
   global total_patients
   global max_queue_lengths 
   global number_triage_queue
   global number_waiting_for_bed_queue  
   global number_workup_queue 
   global number_specialist_queue
   global number_of_beds_per_zone
   global interrupt_lists
   global bed_queue_lists
   global workup_queue_lists
   global triage_queue_list
   global specialist_queue_list
   global time_weighted_queue
   global server_uptime
   global total_interrupts
   global available_ambulances
   global diverted_ambulances
   global time_in_diversion

   clock = 0
   
   available_ambulances = 10
   diverted_ambulances = 0

   # FEL starts off with an arrival of both ambulance and walk-in at t = 0
   initial_ambulance_patient = Patient(arrival_type=0)
   initial_walkin_patient = Patient(arrival_type=1)
   available_ambulances -= 1
   fel = [DepartureAmbulanceEvent(time=0, patient=initial_ambulance_patient), 
          WalkInArrivalEvent(time=0, patient=initial_walkin_patient)]

   # Set number of servers available for each process
   max_num_servers = {
       "doctors":2,
       "nurses":2,
       "specialists":5,
   }

   # Set number of beds available per zone
   number_of_beds_per_zone = {
      1 : 12,
      2 : 8, 
      3 : 10, 
      4 : 10, 
   }

   # State Variables - Resource Statuses
   status_workup_doctors = 0
   status_triage_nurses = 0
   status_specialists = 0

   # State Variables - Queues
   number_triage_queue = 0
   number_waiting_for_bed_queue = 0
   number_workup_queue = 0
   number_specialist_queue = 0

   # Lists of the patients interrupted by higher priority patients
   interrupt_lists = {
      "2":[],
      "3,4,5":[],
   }
   # List of the patients waiting for beds
   bed_queue_lists = {
      "1":[],
      "2":[],
      "3,4,5":[]
   }
   # List of the patients in beds waiting for initial workup assessment
   workup_queue_lists = {
      "1": [],
      "2": [],
      "3,4,5": []
   }
   #List of the patients in the triage queue
   triage_queue_list = []
   # List of patients waiting to see specialist
   specialist_queue_list = []

   ######## Statistics to collect and update ########
   total_interrupts = 0

   total_patients = {
       "in":0,
       "out":0,
   }
   
   max_queue_lengths = {
       "Triage": 0,
       "Bed": 0,
       "Workup": 0,
       "Specialist": 0
   }

   time_weighted_queue = {
       "Triage": [],
       "Bed": [],
       "Workup": [],
       "Specialist": [],
   }

   server_uptime = {
       "Triage": [],
       "Workup": [],
       "Specialist": [],
   }

   time_in_diversion = []
   ##################################################
   def check_bed_queue(zone, patient):
      """
      Helper method used to remove patients waiting for a bed from the queue when another
      patient exits the system (i.e., freeing up a bed).

      Depending on the zone, first check if there is a queued patient that can go into that zone.
      If there is an applicable patient, assign them to the zone and generate their departure
      event for intial workup.
      """
      def give_bed_queued_patient(triage_type):
         global number_workup_queue

         patient.assign_bed_in_zone(zone)
         if status_workup_doctors == max_num_servers["doctors"]:
            number_workup_queue += 1
            workup_queue_lists[triage_type].append(patient)
         else:
            workup_service_time = generate_workup_service_time(patient=patient)
            fel.append(DepartureWorkupEvent(patient=patient, time=clock+workup_service_time))
         return
      
      if zone in {3,4}:
         # Zone 3 or 4 only serves patients of type 2,3,4,5 
         if len(bed_queue_lists["2"]) > 0:
            patient = bed_queue_lists["2"].pop()
            give_bed_queued_patient("2")

         elif len(bed_queue_lists["3,4,5"]) > 0:
            patient = bed_queue_lists["3,4,5"].pop()
            give_bed_queued_patient("3,4,5")

      elif zone in {2}:
         # Zone 2 only serves patients of type 1,2
         if len(bed_queue_lists["1"]) > 0:
            patient = bed_queue_lists["1"].pop()
            give_bed_queued_patient("1")

         elif len(bed_queue_lists["2"]) > 0:
            patient = bed_queue_lists["2"].pop()
            give_bed_queued_patient("2")

      else:
         # Zone 1 only serves patients of type 1
         if len(bed_queue_lists["1"]) > 0:
            patient = bed_queue_lists["1"].pop()
            give_bed_queued_patient("1")
      return
   
   def assign_type_3_4_5_patient_to_zone(patient: Patient, zone):
      """
      Helper method used to assign patients of type 3, 4, or 5 to a zone in the ED. There
      is no priority interrupting between these types of patients.
      """
      global status_workup_doctors
      global number_workup_queue

      number_of_beds_per_zone[zone] -= 1 # Decrease number of available beds

      patient.assign_bed_in_zone(zone)
      if status_workup_doctors == max_num_servers["doctors"]: # Check for available doctors
         number_workup_queue += 1
         workup_queue_lists["3,4,5"].append(patient)
      else:
         status_workup_doctors += 1
         patient.assign_bed_in_zone(zone)
         workup_service_time = generate_workup_service_time(patient)
         fel.append(DepartureWorkupEvent(patient=patient, time=clock + workup_service_time))   
      return

   def handle_arrival_event(event):
      """
         Method used to handles patient arrival events. Handling varies depending on arrival type 
         (ambulance or walk-in). Triage type (1-5) is pre-determined for ambulance arrivals and walk-in 
         patients must get serviced by triage nurses to determine their triage priority.
         
         Triage types 1 and 2 only occur as ambulance arrivals and type 5 only occur as walk-in patients.

         To establish a process for priority, patients types 1 and 2 are capable of interrupting types 
         lower than them, where they will seize the doctor currently serving another patient.
      """
      global status_triage_nurses
      global number_triage_queue
      global number_waiting_for_bed_queue
      global available_ambulances
      global diverted_ambulances

      ################################## ARRIVAL EVENT HELPER METHODS ################################
      
      def assign_type_1_2_patient_to_zone(patient:Patient, zone):
         """
         Helper method used to assign patients of type 1 or 2 to a zone in the ED. These patients
         can interrupt other patients of lower priority in service, but cannot interrupt their own
         priority type.
         """
         global status_workup_doctors
         global total_interrupts

         number_of_beds_per_zone[zone] -= 1
         patient.assign_bed_in_zone(zone)
         workup_service_time = generate_workup_service_time(patient)
         if status_workup_doctors == max_num_servers["doctors"]:
            # If all doctors are busy, attempt to interrupt lower priority patient
            isInterrupted = patient_interrupt(patient, workup_service_time, clock)
            if isInterrupted:
                total_interrupts += 1
                patient.assign_bed_in_zone(zone)
                fel.append(DepartureWorkupEvent(patient = patient, time = clock + workup_service_time))    
         else:
            status_workup_doctors += 1
            patient.assign_bed_in_zone(zone)
            fel.append(DepartureWorkupEvent(patient = patient, time = clock + workup_service_time))    
         return

      def patient_interrupt(patient: Patient, workup_service_time, clock):
         """
         Helper method used by type 1 and 2 patients to find and interrupt patients of lower
         priority (i.e. greater number triage type).

         If there are no patients of lower priority, the pateint gets add to the workup queue.
         """
         global number_workup_queue

         event_to_interrupt = None
         for index, event in enumerate(fel):
              # Only attempt to interrupt DepartureWorkupEvents (type 1)
              if event.type == 5 and event.patient.triage_type < patient.triage_type:
                  interrupted_patient = event.patient
                  if interrupted_patient.triage_type == 2:
                     interrupt_lists["2"].append(interrupted_patient)
                  else: 
                     interrupt_lists["3,4,5"].append(interrupted_patient)
                  event_to_interrupt = index
                  # fel.append(DepartureWorkupEvent(patient=patient, time = clock + workup_service_time))
                  break
         if event_to_interrupt:
            fel.pop(event_to_interrupt)
         else:
            # Can only be a type 1 or 2 patient that failed to interrupt
            workup_queue_lists[str(patient.triage_type)].append(patient)
            number_workup_queue += 1
         return True if event_to_interrupt else False
      ###################################################################################################

      # Generate next arrival event
      arrival_type = event.patient.arrival_type
      
      a = generate_interarrival_time(clock, arrival_type)

      if arrival_type == 0: # Ambulance arrival
         available_ambulances += 1
         if (event.diverted_ambulance): # If diverted, ambulance arrives with no patient
            diverted_ambulances -= 1
            update_simulation_statistics(event)
            return
      else:
          # Generate next walk-in arrival event
          fel.append(WalkInArrivalEvent(time=clock + a, patient=Patient(arrival_type=arrival_type)))

      patient = event.patient
      if (arrival_type == 0):
         if patient.triage_type == 3 or patient.triage_type == 4:
            if number_of_beds_per_zone[3] > 0:
               assign_type_3_4_5_patient_to_zone(patient, 3)
            elif number_of_beds_per_zone[4] > 0:
               assign_type_3_4_5_patient_to_zone(patient, 4)
            else:
               number_waiting_for_bed_queue += 1
               bed_queue_lists["3,4,5"].append(patient)

         elif patient.triage_type == 2:
               if number_of_beds_per_zone[2] > 0:
                  assign_type_1_2_patient_to_zone(patient, 2)
               elif number_of_beds_per_zone[3] > 0:
                  assign_type_1_2_patient_to_zone(patient, 3)
               elif number_of_beds_per_zone[4] > 0:
                  assign_type_1_2_patient_to_zone(patient, 4)
               else:
                  number_waiting_for_bed_queue += 1
                  bed_queue_lists["2"].append(patient)

         else: # Patient type 1
               if number_of_beds_per_zone[1] > 0:
                  assign_type_1_2_patient_to_zone(patient, 1)
               elif number_of_beds_per_zone[2] > 0:
                  assign_type_1_2_patient_to_zone(patient, 2)
               else:
                  number_waiting_for_bed_queue += 1
                  bed_queue_lists["1"].append(patient)

      else: # Walk-in patient arrives, patient goes to triage first
          if status_triage_nurses == max_num_servers["nurses"]:
              number_triage_queue += 1
              triage_queue_list.append(patient)
          else:
              status_triage_nurses += 1
              patient.assign_triage_type(triage_type=generate_walk_in_triage_type())
              triage_time = generate_triage_time(patient) 
              fel.append(DepartureTriageEvent(patient=patient, time=clock+triage_time))

      total_patients["in"] += 1       
      update_simulation_statistics(event)
      return

   def handle_ambulance_departure_event(event: DepartureAmbulanceEvent):
       """
       Method used to handle ambulance departure event to go and assess patient. If there are available 
       ambulances, the patient will be assigned to one. If the triage type is 1 or 2, patients will go to 
       the hospital no matter what. if the triage type is 3 or 4, patients will go to the hospital if there is 
       less than 5 other patients waiting in queue for a bed; otherwise, the ambulance will get diverted to another
       hospital.
       """
       global available_ambulances
       global diverted_ambulances

       a = generate_interarrival_time(clock, 0)
       fel.append(DepartureAmbulanceEvent(time=clock + a, patient=Patient(arrival_type=0)))

       travel_time = np.random.triangular(5, 10, 20, 1)[0]
       process_time = np.random.uniform(4, 10)
       triage_type = generate_ambulance_arrival_triage_type()

       event.patient.assign_triage_type(triage_type=triage_type)
       if (available_ambulances > 0):
            available_ambulances -= 1
            if ((triage_type in {1,2}) or (number_waiting_for_bed_queue < 5 and triage_type in {3,4})):
               fel.append(AmbulanceHospitalArrivalEvent(time=clock + travel_time*2 + process_time, patient=event.patient))
            else:
               diverted_ambulances += 1
               diverted_travel_time = np.random.triangular(10, 15, 25, 1)[0]
               fel.append(AmbulanceHospitalArrivalEvent(time=clock+travel_time+process_time+diverted_travel_time, patient=event.patient, diverted_ambulance=True))
       update_simulation_statistics(event)
       return

   def handle_triage_departure(event: DepartureTriageEvent):
      """
      Method used to handle a walk-in patient's departure from triage. Uses similar methods as arrival 
      eventsusing the following logic: If a bed is free, assign patient to it; otherwise append to a 
      queue waiting for bed.
      """
      global number_waiting_for_bed_queue
      global number_triage_queue
      global status_triage_nurses
      
      status_triage_nurses -= 1
      if number_of_beds_per_zone[4] > 0:
          assign_type_3_4_5_patient_to_zone(event.patient, 4)
      elif number_of_beds_per_zone[3] > 0:
          assign_type_3_4_5_patient_to_zone(event.patient, 3)
      else:
          number_waiting_for_bed_queue += 1
          bed_queue_lists["3,4,5"].append(event.patient)
   
      if len(triage_queue_list) != 0:
          patient = triage_queue_list.pop(0)
          number_triage_queue -= 1
          status_triage_nurses += 1
          patient.assign_triage_type(triage_type=generate_walk_in_triage_type())
          triage_time = generate_triage_time(patient)  
          fel.append(DepartureTriageEvent(patient=patient, time=clock+triage_time))

      update_simulation_statistics(event)
      return

   def handle_workup_departure(event: DepartureWorkupEvent):
      """
      Method used to handle a departure from the initial workup event. The first step 
      is to check for previously interrupted lower priority patients and re-generate their
      workup departure event. If there are none, then check for queued workup patients and
      generate their workup departure events.

      Patients will then be sent to a specialist where they will receive tailored treatment/tests.
      """
      global status_workup_doctors
      global number_workup_queue
      ############################# WORKUP DEPARTURE EVENT HELPER METHODS ################################
      def service_waiting_patient(list: list): 
         """
         Helper method used to generate a departure event for an interrupted or queued patient.
         """
         global status_workup_doctors
         
         patient = list.pop(0)
         status_workup_doctors += 1
         workup_service_time = generate_workup_service_time(patient=patient)
         fel.append(DepartureWorkupEvent(patient=patient, time = clock + workup_service_time))
         return

      def handle_specialist_event(patient):
         """
         Helper method used to generate a specialist departure event
         """
         global status_specialists
         global number_specialist_queue

         if status_specialists == max_num_servers["specialists"]:
             number_specialist_queue += 1
             specialist_queue_list.append(patient)
         else:
             status_specialists += 1
             specialist_service_time = generate_procedure_time(patient)
             fel.append(DepartureSpecialistEvent(patient = patient, time = clock + specialist_service_time))
         return
      ###################################################################################################
     
      status_workup_doctors -= 1

      # Check for any interrupted patients and generature departure event if applicable
      if len(interrupt_lists["2"]) != 0:
         service_waiting_patient(interrupt_lists["2"])
      elif len(interrupt_lists["3,4,5"]) != 0:
         service_waiting_patient(interrupt_lists["3,4,5"])  

      # If there is a doctor still idle, check for queued patient and generate departure event if applicable
      if status_workup_doctors < max_num_servers["doctors"]:
          if len(workup_queue_lists["1"]) != 0:
            service_waiting_patient(workup_queue_lists["1"])
            number_workup_queue -= 1
          elif len(workup_queue_lists["2"]) != 0:
            service_waiting_patient(workup_queue_lists["2"])
            number_workup_queue -= 1
          elif len(workup_queue_lists["3,4,5"]) != 0:
            service_waiting_patient(workup_queue_lists["3,4,5"])
            number_workup_queue -= 1
      
      handle_specialist_event(event.patient)
      update_simulation_statistics(event)
      return

   def handle_specialist_departure(event: DepartureSpecialistEvent):
      """
      Method used to handle a patient's departure from the specialist assessment
      event. This involves freeing up the status of a specialist and the bed in the
      zone of the current patient. 
      
      If there is a patient in the specialist queue, a specialist departure event is 
      created for that patient.
      """
      global status_specialists
      global number_specialist_queue
      
      status_specialists -= 1
      # Check to see if there is a patient in the specialist queue
      if number_specialist_queue > 0:
          status_specialists += 1
          number_specialist_queue -= 1
          queued_patient = specialist_queue_list.pop(0)
          specialist_service_time = generate_procedure_time(event.patient)
          
          # Generate a departure event for the queued patient
          fel.append(DepartureSpecialistEvent(patient = queued_patient, time = clock + specialist_service_time))
      
      # Free up one bed from the zone of the departing patient
      total_patients["out"] += 1
      number_of_beds_per_zone[event.patient.zone] += 1

      check_bed_queue(event.patient.zone, event.patient)

      update_simulation_statistics(event)
      return

   def update_simulation_statistics(event):
       """
       Method used to update counters and calculate statistics called after each event.
       """
       delta_t = event.time - prev_event_time
       if (event.time > 20160):
         # Average queue length
         time_weighted_queue["Triage"].append(delta_t * number_triage_queue)
         time_weighted_queue["Bed"].append(delta_t * number_waiting_for_bed_queue)
         time_weighted_queue["Workup"].append(delta_t * number_workup_queue)
         time_weighted_queue["Specialist"].append(delta_t * number_specialist_queue)

         # Diverted Ambulance
         time_in_diversion.append(delta_t * diverted_ambulances)
         
         # Maximum queue length
         max_queue_lengths["Triage"] = max(max_queue_lengths["Triage"], number_triage_queue)
         max_queue_lengths["Bed"] = max(max_queue_lengths["Bed"], number_waiting_for_bed_queue)
         max_queue_lengths["Workup"] = max(max_queue_lengths["Triage"], number_workup_queue)
         max_queue_lengths["Specialist"] = max(max_queue_lengths["Triage"], number_specialist_queue)
      
         # Server uptime
         server_uptime["Triage"].append(delta_t * status_triage_nurses)
         server_uptime["Workup"].append(delta_t * status_workup_doctors)
         server_uptime["Specialist"].append(delta_t * status_specialists)

       return

   while clock <= simulation_time:
      event = fel.pop(0)
      prev_event_time = clock
      clock = event.time
            
      if event.type == 0 or event.type == 1: # Walk In or Ambulance Arrival
         handle_arrival_event(event)
      elif event.type == 3: # Ambulance Hospital Departure
          handle_ambulance_departure_event(event)
      elif event.type == 4: # Departure from Triage
         handle_triage_departure(event)
      elif event.type == 5: # Departure from Initial Workup Assessment
         handle_workup_departure(event)
      else: # Departure from Specialist Assessment (i.e. Departure from ED)
         handle_specialist_departure(event)
      
      fel.sort(key=lambda x: x.time, reverse = False)
   
   # print("\nNumber of doctors: ", max_num_servers["doctors"])
   # print("Number of triage nurses: ", max_num_servers["nurses"])
   # print("Number of specialists: ", max_num_servers["specialists"], "\n")

   # End of Simulation - Statistic Calculations
   time_weighted_average_queues = {
      "Triage": sum(time_weighted_queue['Triage'])/clock,
      "Bed": sum(time_weighted_queue['Bed'])/clock,
      "Workup": sum(time_weighted_queue["Workup"])/clock,
      "Specialist": sum(time_weighted_queue["Specialist"])/clock
   }

   average_queue_time_per_customer = {
       "Triage": sum(time_weighted_queue['Triage'])/total_patients["out"],
       "Bed": sum(time_weighted_queue['Bed'])/total_patients["out"],
       "Workup": sum(time_weighted_queue["Workup"])/total_patients["out"],
       "Specialist": sum(time_weighted_queue["Specialist"])/total_patients["out"]    
   }

   total_server_uptime = {
       'Triage': sum(server_uptime['Triage']),
       'Workup': sum(server_uptime['Workup']),
       'Specialist': sum(server_uptime['Specialist'])
   }

   server_utilization_rate = {
       'Triage': (sum(server_uptime['Triage'])/(max_num_servers['nurses'] * clock)) * 100,
       'Workup': (sum(server_uptime['Workup'])/(max_num_servers['doctors'] * clock)) * 100,
       'Specialist': (sum(server_uptime['Specialist'])/(max_num_servers['specialists'] * clock)) * 100
   }

   server_idle_rate = {
       'Triage': (1 - (sum(server_uptime['Triage'])/(max_num_servers['nurses'] * clock))) * 100,
       'Workup': (1 - (sum(server_uptime['Workup'])/(max_num_servers['doctors'] * clock))) * 100,
       'Specialist': (1 - (sum(server_uptime['Specialist'])/(max_num_servers['specialists'] * clock))) * 100
   }

   time_percentage_of_ambulances_in_diversion = sum(time_in_diversion)/(10 * clock) * 100

   return {'Time Weighted Average Queues':time_weighted_average_queues, 
           'Average Queue Time Per Customer': average_queue_time_per_customer, 
           'Max Queue Lengths': max_queue_lengths,
           'Total Server Uptime': total_server_uptime,
           'Server Utilization Rate': server_utilization_rate,
           'Server Idle Rate': server_idle_rate,
           'Percentage of Time Ambulances Spent in Diversion': {'Ambulance Diversion':time_percentage_of_ambulances_in_diversion}}

def main():
   number_of_replications = 10
   simulation_time = 24 * 60 * 180
   accumulated_results = []

   for i in range(number_of_replications):
      sim_results = emergency_department_simulation(simulation_time)
      accumulated_results.append(sim_results)

    # Calculate average across all simulations
   average_results = {}
   for metric in accumulated_results[0].keys():
      average_results[metric] = {
         key: sum(result[metric][key] for result in accumulated_results) / number_of_replications
         for key in accumulated_results[0][metric].keys()
      }  

   return average_results

if __name__ == '__main__':
   statistics = main()
   for key,value in statistics.items():
       print(f'Statistic: {key}\nProcess/Server: {value}\n\n')
   