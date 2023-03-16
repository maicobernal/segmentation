import os
import sys
import datetime
import time
import shutil
import subprocess

import numpy as np
import pydicom

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from inference.UNetInferenceAgent import UNetInferenceAgent

def load_dicom_volume_as_numpy_from_list(dcmlist):
    """Loads a list of PyDicom objects a Numpy array.
    Assumes that only one series is in the array

    Arguments:
        dcmlist {list of PyDicom objects} -- path to directory

    Returns:
        tuple of (3D volume, header of the 1st image)
    """

    # In the real world you would do a lot of validation here
    slices = [np.flip(dcm.pixel_array).T for dcm in sorted(dcmlist, key=lambda dcm: dcm.InstanceNumber)]

    # Make sure that you have correctly constructed the volume from your axial slices!
    hdr = dcmlist[0]

    # We return header so that we can inspect metadata properly.
    # Since for our purposes we are interested in "Series" header, we grab header of the
    # first file (assuming that any instance-specific values will be ighored - common approach)
    # We also zero-out Pixel Data since the users of this function are only interested in metadata
    hdr.PixelData = None
    return (np.stack(slices, 2), hdr)

def get_predicted_volumes(pred):
    """Gets volumes of two hippocampal structures from the predicted array

    Arguments:
        pred {Numpy array} -- array with labels. Assuming 0 is bg, 1 is anterior, 2 is posterior

    Returns:
        A dictionary with respective volumes
    """

    # TASK: Compute the volume of your hippocampal prediction
    volume_ant = int(np.sum(pred[pred == 1]))
    volume_post = int(np.sum(pred[pred == 2])/2)
    total_volume = volume_ant + volume_post

    dictionary_volumes = {"anterior": volume_ant, "posterior": volume_post, "total": total_volume}
    print(dictionary_volumes)
    return dictionary_volumes

def create_report(inference, header, orig_vol, pred_vol):
    """Generates an image with inference report

    Arguments:
        inference {Dictionary} -- dict containing anterior, posterior and full volume values
        header {PyDicom Dataset} -- DICOM header
        orig_vol {Numpy array} -- original volume
        pred_vol {Numpy array} -- predicted label

    Returns:
        PIL image
    """

    pimg = Image.new("RGB", (1000, 1000))
    draw = ImageDraw.Draw(pimg)

    header_font = ImageFont.truetype("assets/Roboto-Regular.ttf", size=40)
    main_font = ImageFont.truetype("assets/Roboto-Regular.ttf", size=20)

    slice_nums = [orig_vol.shape[2]//3, orig_vol.shape[2]//2, orig_vol.shape[2]*3//4] # is there a better choice?


    draw.text((10, 0), "HippoVolume.AI", (255, 255, 255), font=header_font)
    draw.multiline_text((10, 90),
                        f"""Patient ID: {header.PatientID}\n
                        Total Images: {header.ImagesInAcquisition}\n
                        Axial Slices: {slice_nums}\n
                        Calculated Total Volume: {inference['total']}\n
                        Calculated Anterior Volume: {inference['anterior']}\n
                        Calculated Posterior Volume: {inference['posterior']}\n
                        """,
                        (255, 255, 255), font=main_font)


    # Numpy array needs to flipped, transposed and normalized to a matrix of values in the range of [0..255]
    orig_norm = (orig_vol/np.max(orig_vol))*0xff
    pred_norm = pred_vol*0xff
    overlay_norm = ((pred_norm+orig_norm)/np.max(pred_norm+orig_norm))*0xff

    dt = datetime.date.today().strftime("%Y%m%d")
    tm = datetime.datetime.now().strftime("%H%M%S")
    
    for n in range(len(slice_nums)):
        nd_img = np.flip(overlay_norm[:,:,slice_nums[n]]).T.astype(np.uint8)

        # This is how you create a PIL image from numpy array
        pil_i = Image.fromarray(nd_img, mode="L").convert("RGBA").resize((300, 400))
        # Paste the PIL image into our main report image object (pimg)
        pimg.paste(pil_i, box=(10+325*n, 400))
        # Save PIL image to out folder
        pil_i.save(os.path.join(".","images", header.PatientID+"_"+dt+"_"+tm+'_slice'+str(slice_nums[n])+'.png'), format= 'png')

    return pimg

def save_report_as_dcm(header, report, path):
    """Writes the supplied image as a DICOM Secondary Capture file

    Arguments:
        header {PyDicom Dataset} -- original DICOM file header
        report {PIL image} -- image representing the report
        path {Where to save the report}

    Returns:
        N/A
    """

    # Set up DICOM metadata fields. Most of them will be the same as original file header
    out = pydicom.Dataset(header)

    out.file_meta = pydicom.Dataset()
    out.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian

    out.is_little_endian = True
    out.is_implicit_VR = False

    # We need to change class to Secondary Capture
    out.SOPClassUID = "1.2.840.10008.5.1.4.1.1.7"
    out.file_meta.MediaStorageSOPClassUID = out.SOPClassUID

    # Our report is a separate image series of one image
    out.SeriesInstanceUID = pydicom.uid.generate_uid()
    out.SOPInstanceUID = pydicom.uid.generate_uid()
    out.file_meta.MediaStorageSOPInstanceUID = out.SOPInstanceUID
    out.Modality = "OT" # Other
    out.SeriesDescription = "HippoVolume.AI"

    out.Rows = report.height
    out.Columns = report.width

    out.ImageType = r"DERIVED\PRIMARY\AXIAL" # We are deriving this image from patient data
    out.SamplesPerPixel = 3 # we are building an RGB image.
    out.PhotometricInterpretation = "RGB"
    out.PlanarConfiguration = 0 # means that bytes encode pixels as R1G1B1R2G2B2... as opposed to R1R2R3...G1G2G3...
    out.BitsAllocated = 8 # we are using 8 bits/pixel
    out.BitsStored = 8
    out.HighBit = 7
    out.PixelRepresentation = 0

    # Set time and date
    dt = datetime.date.today().strftime("%Y%m%d")
    tm = datetime.datetime.now().strftime("%H%M%S")
    out.StudyDate = dt
    out.StudyTime = tm
    out.SeriesDate = dt
    out.SeriesTime = tm

    out.ImagesInAcquisition = 1

    # We empty these since most viewers will then default to auto W/L
    out.WindowCenter = ""
    out.WindowWidth = ""

    # Data imprinted directly into image pixels is called "burned in annotation"
    out.BurnedInAnnotation = "YES"

    out.PixelData = report.tobytes()

    pydicom.filewriter.dcmwrite(path, out, write_like_original=False)

def get_series_for_inference(path):
    """Reads multiple series from one folder and picks the one
    to run inference on.

    Arguments:
        path {string} -- location of the DICOM files

    Returns:
        Numpy array representing the series
    """

    # Here we are assuming that path is a directory that contains a full study as a collection
    # of files
    # We are reading all files into a list of PyDicom objects so that we can filter them later
    dicoms = [pydicom.dcmread(os.path.join(path, f)) for f in os.listdir(path)]

    series_for_inference = [f for f in dicoms if f.SeriesDescription == "HippoCrop"]

    # Check if there are more than one series (using set comprehension).
    if len({f.SeriesInstanceUID for f in series_for_inference}) != 1:
        print("Error: can not figure out what series to run inference on")
        return []

    return series_for_inference

def os_command(command):
    # Run the command directly without an interactive shell
    subprocess.run(command, shell=True)

if __name__ == "__main__":
    # This code expects a single command line argument with link to the directory containing
    # routed studies
    if len(sys.argv) != 2:
        print("You should supply one command line argument pointing to the routing folder. Exiting.")
        sys.exit()

    # Find all subdirectories within the supplied directory. We assume that 
    # one subdirectory contains a full study
    subdirs = [os.path.join(sys.argv[1], d) for d in os.listdir(sys.argv[1]) if
                os.path.isdir(os.path.join(sys.argv[1], d))]

    # Get the latest directory
    study_dir = sorted(subdirs, key=lambda dir: os.stat(dir).st_mtime, reverse=True)[0]

    print(f"Looking for series to run inference on in directory {study_dir}...")

    volume, header = load_dicom_volume_as_numpy_from_list(get_series_for_inference(study_dir))
    print(f"Found series of {volume.shape[2]} axial slices")

    print("HippoVolume.AI: Running inference...")
    
    ## UNet inference
    inference_agent = UNetInferenceAgent(
        device="cpu",
        parameter_file_path=r"./assets/model/model.pth")

    # Run inference
    pred_label = inference_agent.single_volume_inference_unpadded(np.array(volume))

    pred_volumes = get_predicted_volumes(pred_label)

    # Create and save the report
    print("Creating and pushing report...")
    report_save_path = f"./report/temp/{header.PatientName}.dcm"

    report_img = create_report(pred_volumes, header, volume, pred_label)
    save_report_as_dcm(header, report_img, report_save_path)

    # Save overlayed images as a new DICOM series
    print("Saving overlayed images as a new DICOM series...")
    overlay_output_dir = "./overlay/"
    os.makedirs(overlay_output_dir, exist_ok=True)

    # Send report and overlayed images to our storage archive
    os_command("storescu localhost 4242 -v -aec Orthanc +r +sd ./report/temp/")
    print('Report sent to storage archive successfully!')

    time.sleep(2)
    shutil.rmtree(study_dir, onerror=lambda f, p, e: print(f"Error deleting: {e[1]}"))

    print(f"Inference successful on {header['SOPInstanceUID'].value}, out: {pred_label.shape}",
        f"volume ant: {pred_volumes['anterior']}, ",
        f"volume post: {pred_volumes['posterior']}, total volume: {pred_volumes['total']}")
    
    print('Waiting for 5 seconds before deleting files...')
    time.sleep(5)
    
    ## Delete files in the data/received folder
    print('Deleting files in the data/received folder...')
    try:
        for file in os.listdir("./data/received"):
            file_path = os.path.join("./data/received", file)
            os.remove(file_path)
    except:
        print('Some files could not be deleted, delete them manually before running the script again.')
        pass

    ## Move files from report/temp folder to report/sent folder
    print('Moving files from report/temp to report/sent...')
    try:
        for file in os.listdir("./report/temp"):
            file_path = os.path.join("./report/temp", file)
            shutil.move(file_path, "../sent")
    except:
        print('Some files could not be moved, move them manually before running the script again.')
        pass
    
    print('All Done in inference.py!')
