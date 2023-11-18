from random import seed, random
import math

class Patient():
    """
      Patient object used to record arrival and triage types of arrived patients
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
    '''
      Event class, subclassed by specific kinds of events. Contains common attributes for events like time,
      patient, and specific type, with methods to set them.
    '''
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

# Triage events for walk-ins
def main():
   # Global clock variable, updated throughout the program
   global clock
   clock = 0
   seed(42)
   # FEL starts off with an arrival at t = 0
   global fel
   fel = [ArrivalEvent(time=0)]

   # State Variables - Resource Statuses
   global status_triage_nurses
   global status_workup_doctors
   global status_specialists
   global total_patients

   global max_queue_lengths 
   
   max_queue_lengths = {
       "Triage": 0,
       "Bed": 0,
       "Workup": 0,
       "Specialist": 0
   }

   total_patients = 0 
   status_workup_doctors = 0  # Max 2 
   status_triage_nurses = 0  # Max 2
   status_specialists = 0  # Max 2

   # State Variables - Queues
   global number_triage_queue
   global number_waiting_for_bed_queue  
   global number_workup_queue 
   global number_specialist_queue
   number_triage_queue = 0
   number_waiting_for_bed_queue = 0
   number_workup_queue = 0
   number_specialist_queue = 0

   global number_of_beds_per_zone
   number_of_beds_per_zone = {
      1 : 4,
      2 : 4, 
      3 : 6, 
      4 : 12, 
   }

   # Lists
   global interrupt_lists
   interrupt_lists = {
      "2":[],
      "3,4,5":[],
   }
   # Number of people waiting for beds
   global bed_queue_lists
   bed_queue_lists = {
      "1":[],
      "2":[],
      "3,4,5":[]
   }
   # Number of people in beds, waiting for initial assessment
   global workup_queue_lists
   workup_queue_lists = {
      "1": [],
      "2": [],
      "3,4,5": []
   }
   
   global specialist_queue_list
   # People waiting to see specialist
   specialist_queue_list = []

   global time_weighted_queue
   time_weighted_queue = {
       "Triage": [],
       "Bed": [],
       "Workup": [],
       "Specialist": [],
   }

   global server_uptime
   server_uptime = {
       "Triage": [],
       "Workup": [],
       "Specialist": [],
   }

   def generate_interarrival_time():
      r = random()
      # Lambda = 4.5 patients / hour, or 4.5/60 patients / minute
      return (math.log(1 - r)/(4.5/60)) * -1

   def generate_triage_time(patient):
      r = random()
      triage_time = None
      if patient.triage_type == 3:
         triage_time = (math.log(1 - r)/(1/1.5)) * -1
      elif patient.triage_type == 4 or patient.triage_type == 5:
         triage_time = (math.log(1 - r)/(1/13)) * -1
      return triage_time
      
   def generate_workup_service_time(patient):
      # Bins for workup times (hours): [0.5, 1.3], [1.3, 2.1], [2.1, 2.9], [2.9, 3.7], [3.7, 4.5], for patients types 1-5
      # Mean workup times (hours): 0.9, 1.7, 2.5, 3.3, 4.1
      r = random()
      workup_service_time = None
      if patient.triage_type == 1:
         workup_service_time = (math.log(1 - r)/(0.9)) * -1 * 60
      elif patient.triage_type == 2:
         workup_service_time = (math.log(1 - r)/(1.7)) * -1 * 60
      elif patient.triage_type == 3:
         workup_service_time = (math.log(1 - r)/(2.5)) * -1 * 60
      elif patient.triage_type == 4:
         workup_service_time = (math.log(1 - r)/(3.3)) * -1 * 60
      else:
         workup_service_time = (math.log(1 - r)/(4.1)) * -1 * 60
      return workup_service_time

   def generate_specialist_time(patient):
      r = random()
      specialist_time = (math.log(1 - r)/(2.5)) * -1 * 60
      r_test = random()
      if r_test <= 0.2:
         test_time = generate_test_time() 
         specialist_time += test_time
      return specialist_time

   def generate_test_time():
      r = random()
      # Uniformly distributed between 20 and 60 minutes
      time = 20 + r * (60-20)
      return time

   def generate_patient_triage_type():
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

   # walk-in patients can only be types 3, 4 or 5
   def generate_walk_in_triage_type():
      r = random()
      triage_type = 0
      if r <= 0.33333:
          triage_type = 3
      elif r <= 0.66667:
          triage_type = 4
      else:
          triage_type = 5  
      return triage_type

   # Assign patients of types 3, 4 and 5 to beds in zones if they are free
   def assign_type_3_4_5_patient_to_zone(patient: Patient, zone):
      global status_workup_doctors
      global number_workup_queue

      number_of_beds_per_zone[zone] -= 1
      if status_workup_doctors == 2:
         print("Doctors are busy\n")
         number_workup_queue += 1
         workup_queue_lists["3,4,5"].append(patient)
         # Collect statistics and update counters
      else:
         status_workup_doctors += 1
         patient.assign_bed_in_zone(zone)
         workup_service_time = generate_workup_service_time(patient)
         fel.append(DepartureWorkupEvent(patient = patient, time = clock + workup_service_time))   

   def handle_arrival_event(clock):
      '''
         Method that handles patient arrivals, depending on their types. Patients types 1 and 2 are capable
         of interrupting types lower than them, where they will seize the doctor currently serving another patient. Patients either arrive by ambulance or by walk-in 
         (type 1 and 2 will only arrive by ambulance, type 5 only arrive by walk-in).
      '''
      global status_triage_nurses
      global number_triage_queue
      global number_waiting_for_bed_queue
      global total_patients
      # Assigning patients types 1 and 2 to zones
      # They will interrupt anyone lower priority, but will not interrupt their own types
      def assign_type_1_2_patient_to_zone(patient:Patient, zone):
         global status_workup_doctors

         number_of_beds_per_zone[zone] -= 1
         workup_service_time = generate_workup_service_time(patient)
         if status_workup_doctors == 2:
            # If doctors are busy, explore possibility that any patients are interrupted
            patient_interrupt(patient, workup_service_time, clock)
         else:
            status_workup_doctors += 1
            patient.assign_bed_in_zone(zone)
            fel.append(DepartureWorkupEvent(patient = patient, time = clock + workup_service_time))                

      # Method to handle types 1 and 2 interrupting any types greater than them
      def patient_interrupt(patient: Patient, workup_service_time, clock):
         event_to_delete = None
         for index, event in enumerate(fel):
              if event.type == 1 and event.patient.triage_type > patient.triage_type:
                  interrupted_patient = event.patient
                  if interrupted_patient.triage_type == 2:
                     interrupt_lists["2"].append(interrupted_patient)
                  else: 
                     interrupt_lists["3,4,5"].append(interrupted_patient)
                  event_to_delete = index
                  fel.append(DepartureWorkupEvent(patient=patient, time = clock + workup_service_time))
                  break                    
         if event_to_delete:
            del fel[event_to_delete]
         else:
            # Can only be a type 1 or 2 patient that failed to interrupt
            workup_queue_lists[str(patient.triage_type)].append(patient)

      a = generate_interarrival_time()
      next_arrival = ArrivalEvent(time=clock + a)
      fel.append(next_arrival)
      r = random()
      # if r < 0.5, patient arrived by ambulance
      if r <= 0.5:
         triage_type = generate_patient_triage_type()
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
         # Patient type 1         
         else:
             if number_of_beds_per_zone[1] > 0:
                 assign_type_1_2_patient_to_zone(patient, 1)
             elif number_of_beds_per_zone[2] > 0:
                 assign_type_1_2_patient_to_zone(patient, 2)
             else:
                 number_waiting_for_bed_queue += 1
                 bed_queue_lists["1"].append(patient)
      # Walk-in patient arrives, patient goes to triage first                             
      else:
          if status_triage_nurses == 2:
              number_triage_queue += 1
          else:
              status_triage_nurses += 1
              triage_type = generate_walk_in_triage_type()
              patient = Patient(arrival_type=1, triage_type=triage_type)
              triage_time = generate_triage_time(patient)              
              fel.append(DepartureTriageEvent(patient=patient, time=clock+triage_time))
      total_patients += 1       
      update_simulation_statistics(event)
      return           

   def handle_triage_departure(event: DepartureTriageEvent):
      '''
         If a bed is free, assign person to it, otherwise append to a queue waiting for bed (types 3, 4, 5)
      '''
      global number_waiting_for_bed_queue
      
      if number_of_beds_per_zone[4] > 0:
          assign_type_3_4_5_patient_to_zone(event.patient, 4)
      elif number_of_beds_per_zone[3] > 0:
          assign_type_3_4_5_patient_to_zone(event.patient, 3)
      else:
          number_waiting_for_bed_queue += 1
          bed_queue_lists["3,4,5"].append(event.patient)
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
      
      def service_waiting_patient(list, zone): 
         """
         Helper method used to generate a departure event for an interrupted or queued patient.
         """
         global status_workup_doctors
         
         status_workup_doctors -= 1
         patient = list[zone].pop(0)
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

         if status_specialists == 2:
             number_specialist_queue += 1
             specialist_queue_list.append(patient)
         else:
             status_specialists += 1
             specialist_service_time = generate_specialist_time(patient=patient)
             fel.append(DepartureSpecialistEvent(patient = patient, time = clock + specialist_service_time)  )
   
      # First check and generature departure event for interrupted patient
      if len(interrupt_lists["2"]) != 0:
         service_waiting_patient(interrupt_lists["2"])
      elif len(interrupt_lists["3,4,5"]) != 0:
         service_waiting_patient("3,4,5")         

      # If there is a doctor still idle, check and generate departure event for queued patient
      if status_workup_doctors < 2:
          if len(workup_queue_lists["1"]) != 0:
            service_waiting_patient(workup_queue_lists["1"])
          elif len(workup_queue_lists["2"]) != 0:
              service_waiting_patient(workup_queue_lists["2"])
          elif len(workup_queue_lists["3,4,5"]) != 0:
              service_waiting_patient(workup_queue_lists["3,4,5"])
      
      if event.patient.triage_type in {3, 4, 5}:
         r = random()
         if r <= 0.3:
            handle_specialist_event(event.patient)
         else:
             # Patient does not need specialist assessment and can depart from ED
             # Free up one bed from the zone of the departing patient
             number_of_beds_per_zone[event.patient.zone] += 1
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
          number_specialist_queue -= 1
          queued_patient = specialist_queue_list.pop(0)
          specialist_service_time = generate_specialist_time(queued_patient)
          
          # Generate a departure event for the queued patient
          fel.append(DepartureSpecialistEvent(patient = queued_patient, time = clock + specialist_service_time))
      
      # Free up one bed from the zone of the departing patient
      number_of_beds_per_zone[event.patient.zone] += 1
      update_simulation_statistics(event)
      return

   def update_simulation_statistics(event):
       delta_t = event.time - prev_it_clock
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
   
   while clock <= 10000:
      event = fel.pop(0)
      prev_it_clock = clock
      clock = event.time
      # REVIEW
      
      if event.type == 0:
          handle_arrival_event(clock)
      elif event.type == 1:
          handle_triage_departure(event)
      elif event.type == 2:
          handle_workup_departure(event)
      else:
          handle_specialist_departure(event)
      
      fel.sort(key=lambda x: x.time, reverse = False)
      print(f'Clock: {clock}')
      # print(f'Number of beds: {number_of_beds_per_zone}')

   time_weighted_average_queues = {
      "Triage": sum(time_weighted_queue['Triage'])/clock,
      "Bed": sum(time_weighted_queue['Bed'])/clock,
      "Workup": sum(time_weighted_queue["Workup"])/clock,
      "Specialist": sum(time_weighted_queue["Specialist"])/clock
   }

   average_queue_time_per_customer = {
       "Triage": sum(time_weighted_queue['Triage'])/total_patients,
       "Bed": sum(time_weighted_queue['Bed'])/total_patients,
       "Workup": sum(time_weighted_queue["Workup"])/total_patients,
       "Specialist": sum(time_weighted_queue["Specialist"])/total_patients    
   }

   total_server_uptime = {
       'Triage': sum(server_uptime['Triage']),
       'Workup': sum(server_uptime['Workup']),
       'Specialist': sum(server_uptime['Specialist'])
   }

   # Divide by two for utilization, since two servers?
   server_utilization_rate = {
       'Triage': (sum(server_uptime['Triage'])/(2 * clock)) * 100,
       'Workup': (sum(server_uptime['Workup'])/(2 * clock)) * 100,
       'Specialist': (sum(server_uptime['Specialist'])/(2 * clock)) * 100
   }

   server_idle_rate = {
       'Triage': (1 - (sum(server_uptime['Triage'])/(2 * clock))) * 100,
       'Workup': (1 - (sum(server_uptime['Workup'])/(2 * clock))) * 100,
       'Specialist': (1 - (sum(server_uptime['Specialist'])/(2 * clock))) * 100
   }
   
   # Number of patients in and out
   # Average wait time per process
   # Average number waiting per process
   # Total time in system
   # Need to calculate server utilization
   
   return time_weighted_average_queues, average_queue_time_per_customer, max_queue_lengths, total_server_uptime, server_utilization_rate, server_idle_rate

if __name__ == '__main__':
   statistics = main()
   print('Triage, Bed, Workup, Specialist')
   for statistic in statistics:
       print(f' : {statistic}')
   