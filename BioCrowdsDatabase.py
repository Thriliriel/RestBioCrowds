from typing import TYPE_CHECKING
import psycopg2
from AgentClass import AgentClass
from CellClass import CellClass
from GoalClass import GoalClass
from ObstacleClass import ObstacleClass
from Vector3Class import Vector3

if TYPE_CHECKING:
	from BioCrowds import BioCrowdsClass

class BioCrowdsDataBase():

	def connect_to_database(self):
		self.conn = psycopg2.connect(host="localhost",
								database="biocrowds",
								user="postgres",
								password="postgres")

	def close_connection(self):
		self.conn.close()

	# execute and commit SQL command
	def commit_sql(self, sql_str):
		cursor = self.conn.cursor()
		cursor.execute(sql_str)
		self.conn.commit()
		cursor.close()

	# execute and commit SQL command using records (vars)
	def commit_sql_records(self, sql_str, records, exec_many:bool):
		cursor = self.conn.cursor()
		if exec_many:
			cursor.executemany(sql_str, records)
		else:
			cursor.execute(sql_str, records)
		self.conn.commit()
		cursor.close()

	# fetch information from database
	def fetch_sql(self, sql_str):
		cursor = self.conn.cursor()
		cursor.execute(sql_str)
		result = cursor.fetchall()
		cursor.close()
		return result

	# clear data based on a ip
	def clear_database(self, ip, close_conn:bool):
		self.commit_sql("delete from config where id = '" + ip + "'")
		self.commit_sql("delete from agents where ip = '" + ip + "'")
		self.commit_sql("delete from goals where id = '" + ip + "'")
		self.commit_sql("delete from obstacles where id = '" + ip + "'")
		self.commit_sql("delete from obstacles_points where id = '" + ip + "'")
		self.commit_sql("delete from cells where id = '" + ip + "'")
		self.commit_sql("delete from agents_paths where id = '" + ip + "'")
		if close_conn:
			self.close_connection()

	# load data to a BioCrowdsClass
	def load_database(self, bio_crowds:"BioCrowdsClass"):
		
		# config
		result_config = self.fetch_sql("SELECT * FROM config where id = '" + bio_crowds.ip + "'")
		bio_crowds.map_size = Vector3(float(result_config[0][1]), float(result_config[0][2]), float(result_config[0][3]))
		bio_crowds.PORC_QTD_Marcacoes = float(result_config[0][4])
		bio_crowds.time_step = float(result_config[0][5])
		bio_crowds.cell_size = float(result_config[0][6])
		if int(result_config[0][7]) == 0:
			bio_crowds.path_planning =  False
		else:
			bio_crowds.path_planning =  True
		bio_crowds.simulation_time = float(result_config[0][8])

		#goals
		result_goals = self.fetch_sql("SELECT id, x, y, z FROM goals where ip = '" + bio_crowds.ip + "'")
		for res in result_goals:
			bio_crowds.goals.append(GoalClass(int(res[0]), Vector3(float(res[1]), float(res[2]), float(res[3]))))


		#obstacles
		result_obstacles = self.fetch_sql("SELECT id FROM obstacles where ip = '" + bio_crowds.ip + "'")
		for res in result_obstacles:
			bio_crowds.obstacles.append(ObstacleClass(int(res[0])))
			
			#points
			result_obs_points = self.fetch_sql(
				"SELECT x, y, z FROM obstacles_points where ip = '"+bio_crowds.ip+"' and id_obstacle = "+str(res[0]))
			for pnt in result_obs_points:
				bio_crowds.obstacles[len(bio_crowds.obstacles)-1].AddPoint(Vector3(float(pnt[0]), float(pnt[1]), float(pnt[2])))

		#agents
		result_agents = self.fetch_sql("SELECT id, x, y, z, goal, radius, maxspeed FROM agents where ip = '" + bio_crowds.ip + "'")
		for res in result_agents:
			goal_id = int(res[4])
			# find first if match or defaults to first goal
			this_goal = next((g for g in bio_crowds.goals if g.id == goal_id), bio_crowds.goals[0])
			this_position = Vector3(float(res[1]), float(res[2]), float(res[3]))
			bio_crowds.agents.append(AgentClass(int(res[0]), this_goal, float(res[5]), float(res[6]), bio_crowds.path_planning, this_position))

			#agent paths
			result_agent_path = self.fetch_sql(
				"SELECT x, y, z FROM agents_paths where ip = '"+bio_crowds.ip+"' and id_agent = "+str(res[0]))
			for pnt in result_agent_path:
				bio_crowds.agents[len(bio_crowds.agents)-1].AddTempPath(Vector3(float(pnt[0]), float(pnt[1]), float(pnt[2])))

		#cells
		result_cells = self.fetch_sql(
			"SELECT name, x, y, z, radius, density, passedAgents FROM cells where ip = '" + bio_crowds.ip + "' order by id asc")
		for res in result_cells:
			bio_crowds.cells.append(CellClass(str(res[0]), Vector3(float(res[1]), float(res[2]), float(res[3])), float(res[4]), float(res[5]), []))

			#passed agents
			pas = str(res[6])
			if pas != "":
				passed = pas.split(',')
				for pa in passed:
					bio_crowds.cells[len(bio_crowds.cells)-1].AddPassedAgent(int(pa))

		#it is loaded, we can clear now
		self.clear_database(ip=bio_crowds.ip, close_conn=False)

	# save data from a BioCrowdsClass
	def save_database(self, bio_crowds:"BioCrowdsClass"):
		
		#config
		sql_string = 'insert into config (id, mapx, mapy, mapz, markerdensity, timestep, cellsize, usepp, simtime) values(%s,%s,%s,%s,%s,%s,%s,%s,%s);'
		records = (bio_crowds.ip, bio_crowds.map_size.x, bio_crowds.map_size.y, bio_crowds.map_size.z, 
				bio_crowds.PORC_QTD_Marcacoes, bio_crowds.time_step, bio_crowds.cell_size, 
				int(bio_crowds.path_planning == True), bio_crowds.simulation_time)		
		self.commit_sql_records(sql_string, records, exec_many=False)

		#goals
		sql_string = 'insert into goals (ip, id, x, y, z) values (%s, %s, %s, %s, %s);'
		records = []
		for gl in bio_crowds.goals:
			rec = [bio_crowds.ip, gl.id, gl.position.x, gl.position.y, gl.position.z]
			records.append(rec)
		self.commit_sql_records(sql_string, records, exec_many=True)

		#obstacles
		for ob in bio_crowds.obstacles:
			sql_string = 'insert into obstacles (ip, id) values (%s, %s);'
			records = (bio_crowds.ip, ob.id)
			self.commit_sql_records(sql_string, records, exec_many=False)

			#obstacle points
			sql_string = 'insert into obstacles_points (ip, id_obstacle, x, y, z) values (%s, %s, %s, %s, %s);'
			records = []
			for po in ob.points:
				rec = [bio_crowds.ip, ob.id, po.x, po.y, po.z]
				records.append(rec)
			self.commit_sql_records(sql_string, records, exec_many=True)

		#agents
		for ag in bio_crowds.agents:
			sql_string = 'insert into agents (ip, id, x, y, z, goal, radius, maxspeed) values (%s, %s, %s, %s, %s, %s, %s, %s);'
			records = [bio_crowds.ip, ag.id, ag.position.x, ag.position.y, ag.position.z, ag.goal.id, ag.radius, ag.maxSpeed]
			self.commit_sql_records(sql_string, records, exec_many=False)
			
			#agent paths
			sql_string = 'insert into agents_paths (ip, id_agent, x, y, z) values (%s, %s, %s, %s, %s);'
			records = []
			for po in ag.path:
				rec = [bio_crowds.ip, ag.id, po.position.x, po.position.y, po.position.z]
				records.append(rec)
			self.commit_sql_records(sql_string, records, exec_many=True)	

		#cells
		sql_string = 'insert into cells (ip, id, name, x, y, z, radius, density, passedAgents) values (%s, %s, %s, %s, %s, %s, %s, %s, %s);'
		records = []
		idc = 0
		for cl in bio_crowds.cells:
			#string for passed agents
			passed = ""
			for pa in cl.passedAgents:
				if passed == "":
					passed += str(pa)
				else:
					passed += "," + str(pa)

			#print(cl.id)
			rec = [bio_crowds.ip, idc, cl.id, cl.position.x, cl.position.y, cl.position.z, cl.cellRadius, cl.density, passed]
			records.append(rec)
			idc += 1
		self.commit_sql_records(sql_string, records, exec_many=True)
