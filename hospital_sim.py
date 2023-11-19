from random import seed, random
import math

class Patient():
    """
      Object used to represent a patient. Each patient gets assigned differentiating attributes
      such as their arrival type, their triage status (1-5), and to a location in the ED.
    """
    def __init__(self, arrival_type=None, triage_type = None, zone=None):
        self.arrival_type = arrival_type
        self.triage_type = triage_type
        self.zone = zone
    
    def assign_patient_arrival_type(self, arrival_type):
        types = {
            0: "ambulance", 
            1: "walk-in"
        }
        self.arrival_type = types[arrival_type]

    def assign_triage_type(self, triage_type):
        self.triage_type = triage_type

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
           0: "Arrival",
           1: "Departure from Triage",
           2: "Departure from Initial Workup",
           3: "Departure from Specialist Assessment"
       }
       return f"Event Type: {types[self.type]}"
 
class ArrivalEvent(Event):
    def __init__(self, time=None, patient=None):
        super().__init__(type=0, patient=patient, time=time)    

class DepartureTriageEvent(Event):
    def __init__(self, patient=None, time=None):
        super().__init__(type=1, patient=patient, time=time)

class DepartureWorkupEvent(Event):
    def __init__(self, patient=None, time=None):
        super().__init__(type=2, patient=patient, time=time)

class DepartureSpecialistEvent(Event):
    def __init__(self, patient=None, time=None):
        super().__init__(type=3, patient=patient, time=time)

class EndSimulationEvent(Event):
    def __init__(self, time=10000):
        super().__init__(type="End Simulation", time=time)

def generate_interarrival_time():
      """
      Generates interarrival time using lambda value of 4.5 patients / hour, 
      or 4.5/60 patients / minute.
      """
      r = random()
      return (math.log(1 - r)/(4.5/60)) * -1

def generate_triage_time(patient):
   """
   Generates service time for triage assessment (only for walk-in patients)
   """
   r = random()
   triage_time_mapping = {3: 1.5, 4: 13, 5: 13}
   return (math.log(1 - r)/(1/triage_time_mapping[patient.triage_type])) * -1
   
def generate_workup_service_time(patient):
   """
   Generates service time for intiial workup assessment. The service time (in hours) is
   divided into bins: [0.5, 1.3], [1.3, 2.1], [2.1, 2.9], [2.9, 3.7], [3.7, 4.5] for patients
   type 1 through 5.

   Mean workup times (in hours): 0.9, 1.7, 2.5, 3.3, 4.1
   """
   r = random()
   workup_service_time_mapping = {
        1: 0.9,
        2: 1.7,
        3: 2.5,
        4: 3.3,
        5: 4.1
    }
   return (math.log(1 - r) / workup_service_time_mapping[patient.triage_type]) * -1 * 60

def generate_specialist_time():
   """
   Generates service time for specialist assessment. 20% of patients will
   also require testing which adds onto the service time.
   """
   r = random()
   specialist_time = (math.log(1 - r)/(2.5)) * -1 * 60
   r_test = random()
   if r_test <= 0.2:
      return specialist_time + generate_test_time() 
   return specialist_time

def generate_test_time():
   """
   Generates services time for running and obtaining test results.
   Uniformaly distributed between 20 and 60 minutes.
   """
   r = random()
   return 20 + r * (60-20)

def generate_ambulance_arrival_triage_type():
   """
   Assigns triage type for ambulance patients (limited to types 1,2,3,4)
   """
   triage_type = None
   r = random()
   if r <= 0.2:
      triage_type = 1
   elif r <= 0.5:
      triage_type = 2
   elif r <= 0.85:
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

   clock = 0
   
   # FEL starts off with an arrival at t = 0
   fel = [ArrivalEvent(time=0)]

   # Set number of servers available for each process
   max_num_servers = {
       "doctors":2,
       "nurses":1,
       "specialists":1,
   }
   # Set number of beds available per zone
   number_of_beds_per_zone = {
      1 : 14,
      2 : 4, 
      3 : 6, 
      4 : 12, 
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

   def handle_arrival_event():
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
              if event.type == 2 and event.patient.triage_type > patient.triage_type:
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
      a = generate_interarrival_time()
      fel.append(ArrivalEvent(time=clock + a))

      r = random()
      if r <= 0.5: # Patient arrived by ambulance
         triage_type = generate_ambulance_arrival_triage_type()
         patient = Patient(arrival_type=0, triage_type=triage_type)
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
          patient = Patient(arrival_type=1)
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

      Patients of triage type 1 and 2 will automatically be sent to a specialist assessment.
      A random distribution will be used to determine if a patients of triage type 3, 4, or 5 
      will be sent to a specialist assessment; otherwise, they will leave the ED system.
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
             specialist_service_time = generate_specialist_time()
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
      
      if event.patient.triage_type in {3, 4, 5}:
         r = random()
         if r <= 0.3:
            handle_specialist_event(event.patient)
         else:
             # Patient does not need specialist assessment and can depart from ED
             # Free up one bed from the zone of the departing patient
             total_patients["out"] += 1
             number_of_beds_per_zone[event.patient.zone] += 1
             check_bed_queue(event.patient.zone, event.patient)
      else:
            # Patients of type 1 and 2 automatically go to specialist 
            
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
          specialist_service_time = generate_specialist_time()
          
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
       # Average queue length
       time_weighted_queue["Triage"].append(delta_t * number_triage_queue)
       time_weighted_queue["Bed"].append(delta_t * number_waiting_for_bed_queue)
       time_weighted_queue["Workup"].append(delta_t * number_workup_queue)
       time_weighted_queue["Specialist"].append(delta_t * number_specialist_queue)
       
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
      
      if event.type == 0: # Arrival
         handle_arrival_event()
         type="Arrival"
      elif event.type == 1: # Departure from Triage
         handle_triage_departure(event)
         type="Triage"
      elif event.type == 2: # Departure from Initial Workup Assessment
         handle_workup_departure(event)
         type="Workup"
      else: # Departure from Specialist Assessment (i.e. Departure from ED)
         handle_specialist_departure(event)
         type="Specialist"
      
      fel.sort(key=lambda x: x.time, reverse = False)

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
       'Specialist': (1 - (sum(server_uptime['Specialist'])/(max_num_servers['doctors'] * clock))) * 100
   }
   
   return {'Time Weighted Average Queues':time_weighted_average_queues, 
           'Average Queue Time Per Customer': average_queue_time_per_customer, 
           'Max Queue Lengths': max_queue_lengths,
           'Total Server Uptime': total_server_uptime,
           'Server Utilization Rate': server_utilization_rate,
           'Server Idle Rate': server_idle_rate}

def main():
   number_of_replications = 100
   simulation_time = 8*60
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
   