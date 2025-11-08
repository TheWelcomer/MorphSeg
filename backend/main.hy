(import flask [Flask send_from_directory])

(setv app (Flask __name__))

(setv frontend-path "../frontend/dist")

(defn [(app.route "/")]
      index []
      (send_from_directory frontend-path "index.html"))

(defn [(app.route "/<path:path>")]
      files [path]
      (send_from_directory frontend-path path))

(app.run :host "localhost"
         :port 8080)
