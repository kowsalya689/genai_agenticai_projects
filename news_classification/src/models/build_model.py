from sklearn.svm import LinearSVC #subject vector machine

 
 
def build_model():
 
    # C = regularization strength; one-vs-rest handles all categories
    return LinearSVC(C=1.0)
