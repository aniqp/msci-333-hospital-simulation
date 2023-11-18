from random import seed, random
import math

class Patient():
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
   global clock
   clock = 0
   seed(42)
   # FEL starts off with an arrival at t = 0
   fel = [ArrivalEvent(time=0)]

   # State Variables - Resource Statuses
   status_triage_nurses = 0  # Max 2
   status_workup_doctors = 0  # Max 2
   status_specialists = 0  # Max 2

   # State Variables - Queues
   number_triage_queue = 0
   number_waiting_for_bed_queue = 0
   number_workup_queue = 0
   number_specialist_queue = 0

   number_of_beds_per_zone = {
      1 : 4,
      2 : 4, 
      3 : 6, 
      4 : 12, 
   }

   # Lists
   interrupt_lists = {
      "2":[],
      "3,4,5":[],
   }
   bed_queue_lists = {
      "1":[],
      "2":[],
      "3,4,5":[]
   }

   workup_queue_lists = {
      "1": [],
      "2": [],
      "3,4,5": []
   }
   specialist_queue_list = []

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

   def assign_type_3_4_5_patient_to_zone(patient: Patient, zone):
      nonlocal status_workup_doctors
      nonlocal number_workup_queue
      
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

      def assign_type_1_2_patient_to_zone(patient:Patient, zone):
         nonlocal status_workup_doctors
         number_of_beds_per_zone[zone] -= 1
         workup_service_time = generate_workup_service_time(patient)
         if status_workup_doctors == 2:
            patient_interrupt(patient, workup_service_time, clock)
         else:
            status_workup_doctors += 1
            fel.append(DepartureWorkupEvent(patient = patient, time = clock + workup_service_time))                

      def patient_interrupt(patient: Patient, workup_service_time, clock):
         nonlocal fel
         nonlocal interrupt_lists
          
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
                  print(f"Adding patient of type {patient.triage_type} to zone 3\n")
                  assign_type_3_4_5_patient_to_zone(patient, 3)
               elif number_of_beds_per_zone[4] > 0:
                  print(f"Adding patient of type {patient.triage_type} to zone 4\n")
                  assign_type_3_4_5_patient_to_zone(patient, 4)
               else:
                  print(f"Adding patient of type {patient.triage_type} to waiting list for bed\n")
                  bed_queue_lists["3,4,5"].append(patient)
         elif patient.triage_type == 2:
              if number_of_beds_per_zone[2] > 0:
                  assign_type_1_2_patient_to_zone(patient, 2)
              elif number_of_beds_per_zone[3] > 0:
                  assign_type_1_2_patient_to_zone(patient, 3)
              elif number_of_beds_per_zone[4] > 0:
                  assign_type_1_2_patient_to_zone(patient, 4)
              else:
                  bed_queue_lists["2"].append(patient)
         # Patient type 1         
         else:
             if number_of_beds_per_zone[1] > 0:
                 assign_type_1_2_patient_to_zone(patient, 1)
             elif number_of_beds_per_zone[2] > 0:
                 assign_type_1_2_patient_to_zone(patient, 2)
             else:
                 bed_queue_lists["1"].append(patient)
      # Walk-in patient arrives, patient goes to triage                             
      else:
          nonlocal status_triage_nurses
          nonlocal number_triage_queue
          if status_triage_nurses == 2:
              number_triage_queue += 1
          else:
              status_triage_nurses += 1
              triage_type = generate_walk_in_triage_type()
              patient = Patient(arrival_type=1, triage_type=triage_type)
              triage_time = generate_triage_time(patient)              
              fel.append(DepartureTriageEvent(patient=patient, time=clock+triage_time))                   

   def handle_triage_departure(event: DepartureTriageEvent):
      if number_of_beds_per_zone[4] > 0:
          assign_type_3_4_5_patient_to_zone(event.patient, 4)
      elif number_of_beds_per_zone[3] > 0:
          assign_type_3_4_5_patient_to_zone(event.patient, 3)
      else:
          bed_queue_lists["3,4,5"].append(event.patient)

   def handle_workup_departure(event: DepartureWorkupEvent):
      def service_waiting_patient(list, zone): 
         status_workup_doctors -= 1
         patient = list[zone].pop(0)
         status_workup_doctors += 1
         workup_service_time = generate_workup_service_time(patient=patient)
         fel.append(DepartureWorkupEvent(patient=patient, time = clock + workup_service_time))
         return
      
      if len(interrupt_lists["2"]) != 0:
         service_waiting_patient(interrupt_lists["2"])
      elif len(interrupt_lists["3,4,5"]) != 0:
         service_waiting_patient("3,4,5")         

      if status_workup_doctors < 2:
          if len(workup_queue_lists["1"]) != 0:
            service_waiting_patient(workup_queue_lists["1"])
          elif len(workup_queue_lists["2"]) != 0:
              service_waiting_patient(workup_queue_lists["2"])

      return
   
   while clock <= 10000:
      event = fel[0]
      # REVIEW
      clock = event.time
      if event.type == 0:
         handle_arrival_event(clock)
      elif event.type == 1:
          handle_triage_departure(event)
      elif event.type == 2:
          handle_workup_departure(event)
      else:
          print("dep3")
      del fel[0]
      fel.sort(key=lambda x: x.time, reverse = False)
      print(fel)
      print(f'Clock: {clock}')

if __name__ == '__main__':
    main()