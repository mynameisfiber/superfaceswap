import cv2
import dlib
import numpy as np

import transform

PREDICTOR_PATH = "data/shape_predictor_68_face_landmarks.dat"
SCALE_FACTOR = 1 

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(PREDICTOR_PATH)


class TooManyFaces(Exception):
    pass

class NoFaces(Exception):
    pass

def get_landmarks(im, min_area=None):
    rects = detector(im, 1)
    if len(rects) == 0:
        raise NoFaces
    for face in rects:
        if face.area() > min_area:
            landmarks = np.array([[p.x, p.y] for p in predictor(im,face).parts()])
            yield face, landmarks

def normalize_landmarks(face, landmarks):
    center = np.asarray([face.center().x, face.center().y])
    landmarks_centered = landmarks[transform.NORM_POINTS][::2] - center
    diff_last_point = landmarks_centered[:-1] - landmarks_centered[1:]
    turning = np.arctan2(diff_last_point[:,1], diff_last_point[:,0])
    return turning

def annotate_landmarks(im, landmarks):
    im = im.copy()
    for idx, point in enumerate(landmarks):
        pos = tuple(point)
        cv2.circle(im, pos, 3, color=(0, 255, 255, 0.5))
    return im

def read_im_and_landmarks(fname, min_area=None):
    im = cv2.imread(fname, cv2.IMREAD_COLOR)
    landmark_gen = get_landmarks(im, min_area=min_area)
    return im, landmark_gen

if __name__ == "__main__":
    from scipy.spatial import KDTree
    print "Making DB"
    landmarks_db = []
    # db_files = ["images/micha_fb{}.jpg".format(i) for i in xrange(1,6)]
    db_files = ['cruz.png', 'trump.jpg']
    for image in db_files:
        db_image, landmarks_gen = read_im_and_landmarks(image)
        landmarks_db.extend([(db_image, f, l) for f,l in landmarks_gen])
    data = [normalize_landmarks(f, l) for _, f,l in landmarks_db]
    database = KDTree(data)

    #for i, (image, face, landmarks) in enumerate(landmarks_db):
    #    im = annotate_landmarks(image, landmarks[transform.ALIGN_POINTS])
    #    cv2.imwrite(
    #        "faces/face_{:04d}.jpg".format(i), 
    #        im[
    #            face.top():face.bottom(),
    #            face.left():face.right()
    #        ]
    #    )

    print "Matching faces"
    image, landmarks_gen = read_im_and_landmarks("images/micha_fb2.jpg")
    for i, (face, landmarks) in enumerate(landmarks_gen):
        norm_landmarks = normalize_landmarks(face, landmarks)
        search = database.query(norm_landmarks)
        print search
        if search[0] > 0:
            closest_match = search[1]
            db_image, db_face, db_landmarks = landmarks_db[closest_match]
            image = transform.faceswap(db_image, db_landmarks, image, landmarks)
        else:
            closest_match = "NA"
        center = (face.center().x, face.center().y)
        cv2.putText(image, str(closest_match), center,
                    fontFace=cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
                    fontScale=1,
                    color=(255, 0, 255))
    cv2.imwrite("matches.jpg", image)