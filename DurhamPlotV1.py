# DurhamPlot
# Native Python/Matplotlib script to plot out key parts of the solution

# Read the data into numpy
import numpy as np
import matplotlib.pyplot as plt
import math
import cv2
import os
import shutil
import subprocess
from pathlib import Path


def run_meangen(
    meangen_executable,
    meangen_input_text=None,
    meangen_input_file=None,
    run_dir='.',
    timeout_seconds=120,
    output_file='stagen.dat',
):
    """Run MEANGEN in a controlled working directory.

    Parameters:
        meangen_executable (str | Path): Path to compiled meangen executable.
        meangen_input_text (str | None): Full text to write to meangen.in.
        meangen_input_file (str | Path | None): Existing input file to copy as meangen.in.
        run_dir (str | Path): Directory where meangen is executed.
        timeout_seconds (int): Max execution time before timeout.
        output_file (str): Expected output produced by meangen.

    Returns:
        dict with execution metadata and output paths.
    """
    if meangen_input_text is None and meangen_input_file is None:
        raise ValueError('Provide meangen_input_text or meangen_input_file.')
    if meangen_input_text is not None and meangen_input_file is not None:
        raise ValueError('Provide only one of meangen_input_text or meangen_input_file.')

    run_path = Path(run_dir).expanduser().resolve()
    exe_path = Path(meangen_executable).expanduser().resolve()

    if not exe_path.is_file():
        raise FileNotFoundError(f'MEANGEN executable not found: {exe_path}')

    run_path.mkdir(parents=True, exist_ok=True)

    meangen_in_path = run_path / 'meangen.in'
    if meangen_input_text is not None:
        meangen_in_path.write_text(meangen_input_text, encoding='utf-8')
    else:
        input_path = Path(meangen_input_file).expanduser().resolve()
        if not input_path.is_file():
            raise FileNotFoundError(f'MEANGEN input file not found: {input_path}')
        shutil.copyfile(input_path, meangen_in_path)

    result = subprocess.run(
        [str(exe_path)],
        cwd=str(run_path),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )

    output_path = run_path / output_file
    success = result.returncode == 0 and output_path.exists()

    return {
        'success': success,
        'returncode': result.returncode,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'run_dir': str(run_path),
        'meangen_in': str(meangen_in_path),
        'output_file': str(output_path),
        'output_exists': output_path.exists(),
    }

def create_a4_ratio_grid(image_paths, output_path):
    # Define preferred layouts (rows, columns)
    preferred_layouts = [(2, 3), (2, 4), (3, 3)]

    # Total number of images
    num_images = len(image_paths)

    # Try to match one of the preferred layouts
    best_fit = None
    for rows, cols in preferred_layouts:
        if rows * cols >= num_images:
            best_fit = (cols, rows)
            break

    # If no preferred layout fits, calculate an A4 ratio grid
    if best_fit is None:
        a4_ratio = math.sqrt(2)
        best_diff = float('inf')
        for cols in range(1, num_images + 1):
            rows = math.ceil(num_images / cols)
            grid_ratio = cols / rows
            diff = abs(grid_ratio - a4_ratio)
            if diff < best_diff:
                best_diff = diff
                best_fit = (cols, rows)

    grid_columns, grid_rows = best_fit

    # Read all images
    images = [cv2.imread(img) for img in image_paths]

    # Get image dimensions (all images are the same size)
    img_height, img_width, _ = images[0].shape

    # Create a white blank image for padding
    blank_image = np.full((img_height, img_width, 3), 255, dtype=np.uint8)

    # Stack images row by row
    rows = []
    for i in range(grid_rows):
        row_images = images[i * grid_columns:(i + 1) * grid_columns]

        # Add white blank images if the last row is incomplete
        while len(row_images) < grid_columns:
            row_images.append(blank_image)

        rows.append(np.hstack(row_images))

    # Stack rows vertically
    grid_image = np.vstack(rows)

    # Save the final grid image
    cv2.imwrite(output_path, grid_image)

    # Delete original files
    for img_path in image_paths:
        os.remove(img_path)
        

def readstagenew(metadataname):
    """	Read key data from the input file to multall open """
    
    print(f"*** Reading {metadataname} file for grid size ***")
    
    axialdata = readnextlines(metadataname,"JM        JLE       JTE")
    #print(axialdata)
    IMKM = readnextlines(metadataname,"IM        KM")
    #print (IMKM)
    KMAX = IMKM[0][1] # extract number of radial points
    IMAX = IMKM[0][0] # extract tangential of radial points
    
    return IMAX,KMAX,axialdata
    
def readnextlines(metadataname,searchtext):
    """ Reads stage_new.dat file and returns numbers in the line after the search text"""

    f = open(metadataname, 'r', encoding='utf-8')
      
    readnextline = False
    data = []
    for line in f:
    
        # Check to see if we have found the line of interest
        if readnextline == True:
            # print(line)
            values = list(map(int, line.split()))
            data.append(values)
            # print(values)
            readnextline = False
            
        # Check for text string preceeding the line of interest
        if searchtext in line:
            # print(line)
            readnextline = True
            
    f.close()        
    return(data)

def calculate_kslices(IMAX,KMAX):
    """	Calculate the k slices you want to plot on: hub, mid and tip """
    kslicenumberlist = [0,int(KMAX/2),KMAX-1] # this is the k plane that you to display (0 = hub, KMAX = tip)
    print("*** k planes to plot***")
    print(kslicenumberlist)

    return kslicenumberlist

def calculate_jvalues(axialdata):
    """	Calculate the j values for the program: leading and trailing edges and j planes"""
    #print("*** relative j plane locations axial data ***")
    #print(axialdata)
    nbladerows = len(axialdata)
    #print("*** number of blade rows ***")
    #print(nbladerows)

    # JM,JLE and JTE are all in relative coordinates
    # or JM doesn't increase as you go along the blade rows
    # possible this is somewhere else in MULTALL but we are here
    # so we put them into absolute values

    # Loop to conver jplanes data to a monotonic series
    adder = 0
    abs_axialdata = []
    for line in axialdata:
    	line = [x+adder for x in line]
    	adder = line[0]
    	abs_axialdata.append(line)
    print("*** j planes information ***")
    print(abs_axialdata)
    JMAX = (np.max(abs_axialdata))
    
    # Find appropriate set of J values to use
    jslicenumberlist = []
    jslicelabellist = []
    # Get labels like Row #, Mid, Row # Exit

    for idx, line in enumerate(abs_axialdata):
        JMID = int((line[1]+2*line[2])/3) # find a suitable midplane value (JLE+JTE)/2
        jslicenumberlist.append(JMID)
        jslicelabellist.append(f"Row {idx+1}: Mid")
        JEXIT = line[0]-3         # find exit plane value (JTE-3)
        jslicenumberlist.append(JEXIT)
        jslicelabellist.append(f"Row {idx+1}: Exit")
        
    print("*** j planes to plot ***")
    print(jslicenumberlist)

    return jslicenumberlist,jslicelabellist,JMAX,abs_axialdata

def find_line_numbers(filename, search_string):
    """
    Finds the line number(s) of a specific string in a file.

    Parameters:
        filename (str): The file to search.
        search_string (str): The string to search for.

    Returns:
        list: A list of line numbers where the string is found.
    """
    line_numbers = []
    total_lines = 0
    with open(filename, 'r') as file:
        for i, line in enumerate(file):  
            total_lines = total_lines + 1
            if search_string in line:
                line_numbers.append(i)
    return total_lines,line_numbers

def remove_lines(lines, search_string):
    # Filter out lines that contain the search string
    lines_to_keep = [line for line in lines if search_string not in line]

    return lines_to_keep

def convert_to_structured_data(variable_names,data,ni,nj,nk):
    # Define structured array dtype
    dtype = [(var, float) for var in variable_names]

    # Create structured array
    structured_data = np.zeros(data.shape[0], dtype=dtype)
    for i, var in enumerate(variable_names):
        structured_data[var] = data[:, i]

    # Reshape the structured array into 3D (I, J, K)
    structured_data_3d = structured_data.reshape((ni, nj, nk), order='F')

    return structured_data_3d


def readtecplotfile(databasename,IMAX,JMAX,KMAX):
    """ Read in tecplot file and return a structure numpy array with the data in it

    You should be able to use the array as follows:
    
    structured_data[i, j, k]["X"]  # Access "X" at index (i, j, k)
    structured_data[:, :, :]["PSTAT"]  # Access all "PSTAT" values

    """

    print(f"*** Reading {databasename} file for data ***")

    #Check to see if we have more than one passage
    search_string = "PASSAGE NUMBER"
    (total_lines,line_numbers) = find_line_numbers(databasename, "PASSAGE NUMBER")
    n_passages = len(line_numbers)
    print(f"Found {n_passages} passages in the file line(s): {line_numbers}")
    
    # Read the file in
    with open(databasename, 'r') as file:
        lines = file.readlines()

    # Extract variables from the header
    for line in lines:
        if line.startswith("Variables"):
            var_line = line
        if line.startswith(" ZONE"):
            zone_line = line
            break
    variable_names = [
        var.strip('"').strip() for var in var_line.split("=")[1].strip().split(",")
    ]
    print ("Found the follow variables in the data file:")
    print (variable_names)

    # Parse I, J, K dimensions
    dimensions = {}
    parts = zone_line.split()
    for idx, part in enumerate(parts):
        if "I=" in part:
            ni = int(parts[idx+1])
        if "J=" in part:
            nj = int(parts[idx+1])
        if "K=" in part:
            nk = int(parts[idx+1])
    
    if IMAX == ni and JMAX == nj and KMAX == nk:
        print ("Good news!  Dimensions in stage_new.dat and tecplot-input.dat match")
    else:
        print ("ERROR: stage_new.dat and tecplot-input.dat have different grid sizes")
        sys.exit()


    # Get rid of text data in the input
    lines = remove_lines(lines, "TITLE")
    lines = remove_lines(lines, "Variables")
    lines = remove_lines(lines, "ZONE T")

    print(f"Processing: {len(lines)} lines of data.")

    n_points = IMAX * JMAX * KMAX
    
    # Now need to put the first two sections into a NumPy Array

    # Load numerical data
    data1 = np.loadtxt(lines[:n_points])
    structured_data1 = convert_to_structured_data(variable_names,data1,ni,nj,nk)
    print (f"Read in first passage data to the following sized numpy array: {structured_data1.shape}")
    print (f"This array uses {structured_data1.nbytes/1000/1000} Megabytes of memory")
    
    # Load a second data set 
    if n_passages > 1:
        data2 = np.loadtxt(lines[n_points:n_points*2])
        structured_data2 = convert_to_structured_data(variable_names,data2,ni,nj,nk)
        print (f"Read in second passage data to the following sized numpy array: {structured_data2.shape}")
        print (f"This array uses {structured_data2.nbytes/1000/1000} Megabytes of memory")
    else:
        print ("ERROR: only one passage detected, this program requires tecplot-input.dat to have >1 passages")
        sys.exit()
        
    return structured_data1,structured_data2

def plotmesh(data1,data2,k):
    """ Produce a plot of the mesh at slice k """
    x = data1[:,:,k]["X"]
    y = data1[:,:,k]["Y"]
    z = data1[:,:,k]["Z"]

    x2 = data2[:,:,k]["X"]
    y2 = data2[:,:,k]["Y"]
    z2 = data2[:,:,k]["Z"]
      
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
   
    # Set aspect ratio to 1
    ax.set_box_aspect((np.ptp(x), np.ptp(y), np.ptp(z)))
    # Set view to look down
    ax.view_init(elev=90, azim=-90, roll=0)
    ax.plot_wireframe(x, y, z, rstride=1, cstride=1,lw=0.25)
    ax.plot_wireframe(x2, y2, z2, rstride=1, cstride=1,lw=0.25)
    
    ax.set_xlabel(r'$x / [m]$', fontsize=15)
    ax.set_ylabel(r'$y / [m]$', fontsize=15)
    ax.set_zlabel(r'$z / [m]$', fontsize=15)
    ax.set_title(f"Computational Mesh at k={k}")

    ax.grid(True)
    plt.savefig(f'mesh_k{k}.png', format="png")
    plt.close()
    

def plotcontour(data,data2,k,variable, titletext,colourmap):
    """ Produce a contour plot at slice k """
    x = data[:,:,k]["X"]
    y = data[:,:,k]["Y"]
    z = data[:,:,k][variable]

    x2 = data2[:,:,k]["X"]
    y2 = data2[:,:,k]["Y"]
    z2 = data2[:,:,k][variable]
    
    
    fig, ax = plt.subplots()
    colourscale = ax.contourf(x, y, z,cmap=colourmap,levels=50)
    colourscale = ax.contourf(x2, y2, z2,cmap=colourmap,levels=50)
    ax.set_xlabel(r'$x / [m]$')
    ax.set_ylabel(r'$y / [m]$')
    ax.set_title(titletext+f" at k={k}")
    ax.axis('equal')
    plt.colorbar(colourscale)

    filename = f'b2b_{variable}_k{k}.png'
    plt.savefig(filename, format="png",dpi=300)
    plt.close()
    return filename

def pressure_vs_chord(data1,data2,k,IMAX,JMAX,KMAX,axialdata):
    """ Produce a pressure vs x plot at a given k plane"""
        
    fig, (ax1, ax2) = plt.subplots(2, 1)
    fig.suptitle(f'Blade Shape and Surface Pressures at k={k}')

    ax1.set_ylabel(r'$y / [m]$')
    ax1.axis('equal')
    ax1.grid(which='both')
    
    ax2.set_xlabel(r'$x / [m]$')
    ax2.set_ylabel(r'$p / [Pa]$')
    ax2.grid(which='both')

    # Variables to hold data for writing later
    xdata = []; y1data =[]; y2data =[]; p1data =[]; p2data =[];
    
    # Step through axial data to find leading and trailing edges
    for n in range(len(axialdata)):
        JLE = axialdata[n][1]
        JTE = axialdata[n][2]
        # print(f"n: {n}, JLE: {JLE}, JTE: {JTE}")

        # Suction and Pressure side alternates from 0 to IMAX-1
        # Switch lines styles on each count 
        if n % 2 ==0:
            linestyle1 = 'b--' # pressure side
            linestyle2 = 'r-' # suction side
        else:
            linestyle1 = 'r-' # suction side
            linestyle2 = 'b--' # pressure side

        # Plot pressures
        ax2.plot(data1[0,JLE:JTE,k]["X"],data1[0,JLE:JTE,k]["PSTAT"],linestyle1)
        ax2.plot(data1[0,JLE:JTE,k]["X"],data1[IMAX-1,JLE:JTE,k]["PSTAT"],linestyle2)

        # Store data to write out later 
        xdata.append(data1[0,JLE:JTE,k]["X"])
        p1data.append(data1[0,JLE:JTE,k]["PSTAT"])
        p2data.append(data1[IMAX-1,JLE:JTE,k]["PSTAT"])

        # Plot blade shapes
        ax1.plot(data1[0,JLE:JTE,k]["X"],data1[IMAX-1,JLE:JTE,k]["Y"],linestyle2)
        ax1.plot(data2[0,JLE:JTE,k]["X"],data2[0,JLE:JTE,k]["Y"],linestyle1)

        # Store data to write out later
        y1data.append(data1[IMAX-1,JLE:JTE,k]["Y"])
        y2data.append(data2[0,JLE:JTE,k]["Y"])
        
    filename = f'pvsx_k{k}.png'
    plt.savefig(filename, format="png",dpi=300)
    plt.close()

    xout = np.concatenate(xdata)
    y1out = np.concatenate(y1data)
    y2out = np.concatenate(y2data)
    p1out = np.concatenate(p1data)
    p2out = np.concatenate(p2data)
    
    output_file = f'pvsx_k{k}.txt'
    with open(output_file, 'w') as f:
        f.write(f"# p vs x data at k={k} \nx [m], y1 [m], y2 [m], p1 [Pa], p2 [Pa]\n")
        for xi, y1i, y2i, p1i, p2i in zip(xout, y1out, y2out, p1out, p2out):
            f.write(f"{xi:.6f}, {y1i:.6f}, {y2i:.6f}, {p1i:.6f}, {p2i:.6f}\n")
    
    return filename

    
def plotmeridionalview(data1,data2,i,axialdata,variable,titletext,colourmap):
    """ Produce some meridional views of the blade"""
    x = data1[i,:,:]["X"]
    y = data1[i,:,:]["Z"]
    z = data1[i,:,:][variable]

    fig, ax = plt.subplots()
    colourscale = ax.contourf(x, y, z,cmap=colourmap,levels=50)

    for n in range(len(axialdata)):
        JLE = axialdata[n][1]
        JTE = axialdata[n][2]
        le_x = data1[i,JLE,:]["X"]
        le_y = data1[i,JLE,:]["Z"]
        te_x = data1[i,JTE,:]["X"]
        te_y = data1[i,JTE,:]["Z"]
        ax.plot(le_x,le_y,'k-')
        ax.plot(te_x,te_y,'k-')
        
    ax.set_xlabel(r'$x / [m]$')
    ax.set_ylabel(r'$z / [m]$')
    ax.set_title(titletext+f" at i={i}")
    ax.axis('equal')
    plt.colorbar(colourscale)
    filename = f'merid_{variable}_i{i}.png'
    plt.savefig(filename, format="png",dpi=300)
    plt.close()
    return filename

def plotvectors(data1,data2,j,IMAX,JMAX,KMAX,abs_axialdata):
    """ Produce vector plot of flow at slice j """

    y = data1[:,j,:]["Y"]
    z = data1[:,j,:]["Z"]    
    v = data1[:,j,:]["VY"]
    w = data1[:,j,:]["VZ"]
    c = data1[:,j,:]["MACH"]

    y2 = data2[:,j,:]["Y"]
    z2 = data2[:,j,:]["Z"]    
    v2 = data2[:,j,:]["VY"]
    w2 = data2[:,j,:]["VZ"]
    c2 = data2[:,j,:]["MACH"]
            
    fig, ax = plt.subplots()
    
    ax.quiver(y,z,v,w,c,width=0.002,cmap='turbo')
    ax.quiver(y2,z2,v2,w2,c2,width=0.002,cmap='turbo')
    
    ax.set_xlabel(r'$y / [m]$')
    ax.set_ylabel(r'$z / [m]$')
    ax.set_title(f"Vector Plot at j={j}, colour is Mach No/[1]")
    ax.axis('equal')
   
    filename = f'vectorplot_j{j}.png'
    plt.savefig(filename, format="png",dpi=300)
    plt.close()
    return filename


def plotcontour_rt(data1,data2,j,variable,titletext,colourmap,labeltext):
    """ Produce a contour plot at slice j """
    x = data1[:,j,:]["Y"]
    y = data1[:,j,:]["Z"]
    z = data1[:,j,:][variable]

    x2 = data2[:,j,:]["Y"]
    y2 = data2[:,j,:]["Z"]
    z2 = data2[:,j,:][variable]
    
    fig, ax = plt.subplots()
    colourscale = ax.contourf(x, y, z,cmap=colourmap,levels=50)
    colourscale = ax.contourf(x2, y2, z2,cmap=colourmap,levels=50)
    ax.set_xlabel(r'$y / [m]$')
    ax.set_ylabel(r'$z / [m]$')
    ax.set_title(titletext+f" at j={j}")
    ax.axis('equal')
    plt.colorbar(colourscale)
    plt.text(0.05, 0.05, labeltext,transform=ax.transAxes,fontsize=12)

    filename = f'rt_{variable}_j{j}.png'
    plt.savefig(filename, format="png",dpi=300)
    plt.close()
    return filename

def main():
    databasename = "tecplot-input.dat"
    metadataname = "stage_new.dat"

    # Get information about the solution from the stage_new.dat file
    IMAX,KMAX,axialdata = readstagenew(metadataname)
    kslicenumberlist = calculate_kslices(IMAX,KMAX)
    jslicenumberlist,jslicelabellist,JMAX,abs_axialdata = calculate_jvalues(axialdata)

    # Read data
    # Can merge data (as below), but two plots means the blade shapes are easier on contours
    # merged_data = np.concatenate((data1, data2), axis=0)
    data1,data2 = readtecplotfile(databasename,IMAX,JMAX,KMAX)

    # Plots to be drawn
    variablelist = ["ENT_FUN","PSTAT","MACH","VX","RHO"] # the variable you want to plot
    colourmaplist = ['viridis','turbo','turbo','turbo','Greys'] # the variable you want to plot
    titletextlist = ["ENT_FUN / [1]","Static Pressure / [Pa]","Mach No / [1]","Axial Velocity / [m/s]","Density / [kg/m^3]"]

    for i in [0,int(IMAX/2),IMAX-1]:
        print(f"Drawing plots at constant i={i}")
        filelist = []
        for (variable, titletext, colourmap) in zip(variablelist,titletextlist,colourmaplist):
            filename = plotmeridionalview(data1,data2,i,abs_axialdata,variable,titletext,colourmap)
            filelist.append(filename)
        create_a4_ratio_grid(filelist,f"iplanes_i{i}.png")

    # Plots to be drawn
    variablelist = ["ENT_FUN","PSTAT","MACH","RHO","YAW","PITCH"] # the variable you want to plot
    colourmaplist = ['viridis','turbo','turbo','Greys','bwr','bwr'] # the variable you want to plot
    titletextlist = ["ENT_FUN / [1]","Static Pressure / [Pa]","Mach No / [1]","Density / [kg/m^3]","Yaw /[deg]","Pitch / [deg]"]

    for (j,label) in zip(jslicenumberlist,jslicelabellist):
        print(f"Drawing plots at constant j={j}")
        filelist = []
        for (variable, titletext, colourmap) in zip(variablelist,titletextlist,colourmaplist):
            filename = plotcontour_rt(data1,data2,j,variable,titletext,colourmap,label)
            filelist.append(filename)
        filename = plotvectors(data1,data2,j,IMAX,JMAX,KMAX,abs_axialdata)
        filelist.append(filename)
        create_a4_ratio_grid(filelist,f"jplanes_j{j}.png")

    # Plots to be drawn
    variablelist = ["ENT_FUN","PSTAT","TSTAT","YAW","MACH","RHO","VX"] # the variable you want to plot
    colourmaplist = ['viridis','turbo','turbo','bwr','turbo','Greys','turbo'] # the variable you want to plot
    titletextlist = ["ENT_FUN / [1]","Static Pressure / [Pa]","Static Temp / [K]","Yaw / [deg]","Mach No / [1]","Density / [kg/m^3]","Axial Velocity / [m/s]"]

    for k in kslicenumberlist:
        print(f"Drawing plots at constant k={k}")
        filelist = []
        for (variable, titletext, colourmap) in zip(variablelist,titletextlist,colourmaplist):
            filename = plotcontour(data1,data2,k,variable, titletext,colourmap)
            filelist.append(filename)
        filename = pressure_vs_chord(data1,data2,k,IMAX,JMAX,KMAX,abs_axialdata)
        filelist.append(filename)
        create_a4_ratio_grid(filelist,f"kplanes_k{k}.png")
        pressure_vs_chord(data1,data2,k,IMAX,JMAX,KMAX,abs_axialdata) # Call this twice so you have big version of this still around
        


    print("All plots drawn")
    

if __name__ == "__main__":
    main()
