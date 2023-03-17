"""
Contains various functions for computing statistics over 3D volumes
"""
import numpy as np

def Dice3d(a, b):
    """
    This will compute the Dice Similarity coefficient for two 3-dimensional volumes
    Volumes are expected to be of the same size. We are expecting binary masks -
    0's are treated as background and anything else is counted as data

    Arguments:
        a {Numpy array} -- 3D array with first volume
        b {Numpy array} -- 3D array with second volume

    Returns:
        float
    """
    if len(a.shape) != 3 or len(b.shape) != 3:
        raise Exception(f"Expecting 3 dimensional inputs, got {a.shape} and {b.shape}")

    if a.shape != b.shape:
        raise Exception(f"Expecting inputs of the same shape, got {a.shape} and {b.shape}")
    
    # Convert input arrays to binary masks
    a_mask = np.where(a > 0, 1, 0)
    b_mask = np.where(b > 0, 1, 0)

    # Calculate intersection and sum of the two binary masks
    intersection = np.sum(a_mask * b_mask)
    total_elements = np.sum(a_mask) + np.sum(b_mask)

    if total_elements == 0:
        return -1
    else:
        return 2 * float(intersection) / float(total_elements)

def Jaccard3d(a, b):
    """
    This will compute the Jaccard Similarity coefficient for two 3-dimensional volumes
    Volumes are expected to be of the same size. We are expecting binary masks - 
    0's are treated as background and anything else is counted as data

    Arguments:
        a {Numpy array} -- 3D array with first volume
        b {Numpy array} -- 3D array with second volume

    Returns:
        float
    """
    if len(a.shape) != 3 or len(b.shape) != 3:
        raise Exception(f"Expecting 3 dimensional inputs, got {a.shape} and {b.shape}")

    if a.shape != b.shape:
        raise Exception(f"Expecting inputs of the same shape, got {a.shape} and {b.shape}")


    # Convert input arrays to binary masks
    a_mask = np.where(a > 0, 1, 0)
    b_mask = np.where(b > 0, 1, 0)

    # Calculate intersection and union of the two binary masks
    intersection = np.sum(a_mask * b_mask)
    union = np.sum(a_mask) + np.sum(b_mask) - intersection

    if union == 0:
        return -1
    else:
        return float(intersection) / float(union)
    

def Sensitivity(a, b):
    """
    This will compute the Sensitivity for two 3-dimensional volumes
    Volumes are expected to be of the same size. We are expecting binary masks - 
    0's are treated as background and anything else is counted as data

    Arguments:
        a {Numpy array} -- 3D array with first volume
        b {Numpy array} -- 3D array with second volume

    Returns:
        float
    """
    if len(a.shape) != 3 or len(b.shape) != 3:
        raise Exception(f"Expecting 3 dimensional inputs, got {a.shape} and {b.shape}")

    if a.shape != b.shape:
        raise Exception(f"Expecting inputs of the same shape, got {a.shape} and {b.shape}")
        
    # Sens = TP/(TP+FN)
    tp = np.sum(a[a==b])
    fn = np.sum(a[a!=b])

    if fn+tp == 0:
        return -1

    return (tp)/(fn+tp)

def Specificity(a, b):
    """
    This will compute the Specificity for two 3-dimensional volumes
    Volumes are expected to be of the same size. We are expecting binary masks - 
    0's are treated as background and anything else is counted as data

    Arguments:
        a {Numpy array} -- 3D array with first volume
        b {Numpy array} -- 3D array with second volume

    Returns:
        float
    """
    if len(a.shape) != 3 or len(b.shape) != 3:
        raise Exception(f"Expecting 3 dimensional inputs, got {a.shape} and {b.shape}")

    if a.shape != b.shape:
        raise Exception(f"Expecting inputs of the same shape, got {a.shape} and {b.shape}")
        
    # Spec = TN/(TN+FP)
    tn = np.sum((a==0)*(b==0))
    fp = np.sum((a!=b)*(b==0))

    if tn+fp == 0:
        return -1

    return (tn)/(tn+fp)