import cherrypy
import pandas as pd
import os
import gc

import cherrypy_cors

import BioCrowds

#cherrypy.config.update({'server.socket_port': 5000})

biocrowds = BioCrowds.BioCrowds()

class RestBioCrowds(object):
	@cherrypy.expose
	@cherrypy.tools.json_out()
	@cherrypy.tools.json_in()
	def runSim(self):
		"""Handle HTTP requests against ``/tokenize`` URI."""
		if cherrypy.request.method == 'OPTIONS':
		#	# This is a request that browser sends in CORS prior to
		#	# sending a real request.

		#	# Set up extra headers for a pre-flight OPTIONS request.
			return cherrypy_cors.preflight(allowed_methods=['GET', 'POST'])

		data = cherrypy.request.json
		#print(data)
		#df = pd.DataFrame(data)
		#output = biocrowds.run(df)
		output = biocrowds.run(data)
		#output.show()
		
		gc.collect()

		return output.to_json()

if __name__ == '__main__':
	cherrypy_cors.install()
	config = {'tools.sessions.timeout': 60, 'server.socket_host': '0.0.0.0', 'server.socket_port': int(os.environ.get('PORT', 5000)), 'cors.expose.on': True} #, 'cors.expose.on': True
	cherrypy.config.update(config)
	cherrypy.quickstart(RestBioCrowds())

#running: 
#curl -d "{\"text\" : [\"i am not feeling good\"]}" -H "Content-Type: application/json" -X POST http://localhost:5000/runSim
#curl -d "{\"text\" : [\"i am not feeling good\"]}" -H "Content-Type: application/json" -X POST https://serene-beach-46283.herokuapp.com/runSim