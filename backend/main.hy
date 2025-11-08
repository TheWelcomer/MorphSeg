(import flask [Flask send_from_directory])

(setv app (Flask __name__))

(defn [(app.route "/")]
      index []
      (send_from_directory "../frontend/public" "index.html"))

(defn [(app.route "/<path:path>")]
      files [path]
      (send_from_directory "../frontend/public" path))

(app.run :host "localhost"
         :port 8080)
