# FaceNet Attendance System - Viva Questions

## Easy Level

**Q1: What is the main objective of this project?**
**A:** To automate the attendance process using facial recognition technology, eliminating manual entry and proxy attendance.

**Q2: Which deep learning model is used for face recognition?**
**A:** **FaceNet**, developed by Google.

**Q3: What framework is used for the web interface?**
**A:** **Flask**, a lightweight web framework for Python.

**Q4: How does the system detect faces in an image?**
**A:** It uses **MTCNN** (Multi-task Cascaded Convolutional Networks), which is very effective at detecting face positioning and landmarks.

**Q5: where is the attendance data stored?**
**A:** The attendance is marked in **Excel sheets** (.xlsx) generated in the `reports` folder. User data is stored in a **SQLite** database.

---

## Medium Level

**Q6: How does FaceNet work?**
**A:** FaceNet maps facial features into a 128-dimensional vector space (embedding). The key idea is that images of the same person should be close to each other in this space, while images of different people should be far apart.

**Q7: What is an "embedding"?**
**A:** An embedding is a numerical representation (a list of numbers) of a face's features. In this project, it's a 128-byte vector. If two vectors are similar (mathematically close), they represent the same face.

**Q8: Why do we use a confidence threshold?**
**A:** To prevent false positives. We set a threshold (e.g., 75%) so that the system only marks attendance if it is very sure the face matches a known student. If the similarity score is too low, it's safer to reject it than to mark the wrong person present.

**Q9: What is "Kiosk Mode"?**
**A:** It refers to a configuration where the application is set up for public/shared use without requiring individual logins. The system is always ready to scan any user who steps up to the camera.

**Q10: How is the live camera feed handled?**
**A:** We use **HTML5 Video** API to stream the webcam in the browser and **JavaScript Canvas** to capture a still frame, which is then sent to the Python server via an AJAX POST request.

---

## Hard Level

**Q11: Explain the "Triplet Loss" function used in FaceNet.**
**A:** Triplet Loss is the training objective for FaceNet. It uses three images: an **Anchor** (A), a **Positive** (P) (same person as A), and a **Negative** (N) (different person). The loss function minimizes the distance between A and P while maximizing the distance between A and N, enforcing that $Distance(A, P) + margin < Distance(A, N)$.

**Q12: How did you handle the migration from TensorFlow 1.x to 2.x?**
**A:** The legacy code used TF 1.x graph execution. To make it work in TF 2.x, we imported `tensorflow.compat.v1` and called `tf.disable_v2_behavior()`. This allows old "Graph" and "Session" based code to run within the modern TF 2 environment.

**Q13: What is the difference between Face Detection and Face Recognition?**
**A:**
- **Detection**: Finding *where* a face is in the image (bounding box). We use MTCNN for this.
- **Recognition**: Identifying *who* the face belongs to. We use FaceNet for this.

**Q14: How does the classifier work after FaceNet generates embeddings?**
**A:** FaceNet only outputs the 128-d numbers. We treat these numbers as inputs to a standard Machine Learning classifier (like an **SVM** or **KNN**, stored in `my_classifier.pkl`). This classifier allows us to assign a specific name/label to that set of numbers.

**Q15: How would you scale this system for 1000 users?**
**A:**
- **Database**: Move from SQLite to PostgreSQL or MySQL.
- **Optimization**: Use a vector database (like Pinecone or Milvus) to search embeddings faster instead of a simple pickle classifier.
- **Hardware**: Use a GPU for faster inference.
