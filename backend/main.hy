(import flask [Flask send_from_directory])

(setv app (Flask __name__))

(setv frontend-path "../frontend/build")

(defmacro serve-page [title]
  `(defn [(app.route (+ "/" ~(str title)))]
         ~title []
         (send_from_directory
           frontend-path 
           (+ ~(str title)
              ".html"))))

(defn [(app.route "/")]
      index []
      (send_from_directory frontend-path "index.html"))

(serve-page showcase)

(defn [(app.route "/<path:path>")]
      files [path]
      (send_from_directory frontend-path path))

(app.run :host "localhost"
         :port 8080)
