# mandelbrot-zoom.py
# This program renders the mandelbrot set on the screen and allows you to zoom in and out with a mouse click.

# Install numpy numba and matplotlib
import numpy as np                                      # NumPy for efficient calculations
from numpy import typing as npt
from numba import vectorize, float64, complex128, int16 # Numba to use the GPU

import matplotlib                                       # Matplotlib for rendering
matplotlib.use('TkAgg') # This is needed on Linux
import matplotlib.pyplot as plt 
from matplotlib.colors import LinearSegmentedColormap, Normalize # Matplotlib colors to define the color map

colors = [(0.0, "#0077B1"), (0.2, "#E63B21"), (0.5, "#F5B220"), (1.0, "#FFE043")]  
mycolormap = LinearSegmentedColormap.from_list("mandelbrot", colors)
mycolormap.set_under('black')

BREADTH, HEIGHT = 1440, 1080  # The canvas size in pixels

@vectorize([float64(complex128, complex128, int16)])
def mandelbrot(z, c, i):
    """Calculates the number of iterations until the Mandelbrot series for the complex number c diverges.

    Args:
        z (complex):    Start value of the Mandelbrot series (usually 0)
        c (complex):    The complex number that is the argument of the mandelbrot function
        i (int):        The upper limit of iterations
    Returns:
        int: The number of iterations until the Mandelbrot series diverges (i.e. exceeds 1000), or -1 if the series does not diverge.
    """
    for n in range(i):
        if abs(z) > 1000:
            return float64(n)
        z = z**2 + c
    return float64(-1)


def compute_mandelbrot(xmin: float, xmax: float, ymin: float, ymax: float) -> npt.NDArray[np.complex128]:
    """Computes the Mandelbrot set for a given range.
    
    Args:
        xmin (float): The lower limit of the real part
        xmax (float): The upper limit of the real part
        ymin (float): The lower limit of the imaginary part
        ymax (float): The upper limit of the imaginary part

    Returns:
        np.array(float): The Mandelbrot set
    """
    global BREADTH, HEIGHT, max_iter
    x = np.linspace(xmin, xmax, BREADTH)    # The real axis
    y = np.linspace(ymin, ymax, HEIGHT)     # The imaginary axis
    c = x + 1j * y[:, np.newaxis]           # The array of complex numbers c = x + yi
    z = np.zeros_like(c)                    # Start value of the Mandelbrot series
    return mandelbrot(z, c, max_iter)       # Calculates the Mandelbrot set for all values in parallel on the GPU


def render(xmin: float, xmax: float, ymin: float, ymax: float) -> None:
    """Rerenders the picture with the new limits after a zoom
    
    Args:
        xmin (float): The lower limit of the real part
        xmax (float): The upper limit of the real part
        ymin (float): The lower limit of the imaginary part
        ymax (float): The upper limit of the imaginary part
    """
    mandelbrot_set = compute_mandelbrot(xmin, xmax, ymin, ymax)
    zmin = mandelbrot_set[mandelbrot_set > 0].min()
    zmax = mandelbrot_set.max()
    picture.set_data(mandelbrot_set)
    picture.set_extent([xmin, xmax, ymin, ymax])
    picture.set_clim(zmin,zmax)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    fig.canvas.draw_idle()


def on_click(event):
    """With a left mouse click, you zoom in by a factor of 5. And with a right mouse click you zoom out by a factor of 5"""
    global xmin, xmax, ymin, ymax, max_iter

    if event.inaxes != ax or event.xdata is None or event.ydata is None:
        return

    xcenter = event.xdata
    ycenter = event.ydata
    
    if event.button == 1:
        max_iter *= 2
        new_breadth = (xmax - xmin) / 5
        new_height = (ymax - ymin) / 5

    else:
        max_iter //= 2
        new_breadth = (xmax - xmin) * 5
        new_height = (ymax - ymin) * 5

    xmin = xcenter - new_breadth / 2
    xmax = xcenter + new_breadth / 2
    ymin = ycenter - new_height / 2
    ymax = ycenter + new_height / 2

    render(xmin, xmax, ymin, ymax)


def on_key_press(event):
    """Saves the picture in high resolution when you press key 't'"""
    global xmin, xmax, ymin, ymax, max_iter, count

    if event.key == 't':
        fig.canvas.manager.set_window_title('Saving picture ... Please WAIT') # Tell the user what is happening
        fig.canvas.draw()
        x = np.linspace(xmin, xmax, 12000)      # The real axis
        y = np.linspace(ymin, ymax, 9000)       # The imaginary axis
        c = x + 1j * y[:, np.newaxis]           # The array of complex numbers c = x + yi
        z = np.zeros_like(c)                    # Start value of the Mandelbrot series
        mandelbrot_set = mandelbrot(z, c, max_iter)       # Calculates the Mandelbrot set for all values in parallel on the GPU
        zmin = mandelbrot_set[mandelbrot_set > 0].min()
        zmax = mandelbrot_set.max()
        fig2, ax2 = plt.subplots(figsize=(20, 15), dpi=600)     # 12000 x 9000 pixels at 600 DPI on a 20x15 inch canvas
        fig2.subplots_adjust(left=0, right=1, bottom=0, top=1)  # The picture shall fill the whole canvas
        ax2.imshow(
            mandelbrot_set,
            extent=[xmin, xmax, ymin, ymax],
            cmap=mycolormap,
            norm=Normalize(vmin=zmin, vmax=zmax, clip=False),
            interpolation="none",
            origin="lower",
        )
        ax2.set_axis_off()  # Do not show axes

        # Save the picture as PNG file under the name "mandelbrot-1.png".
        fig2.savefig(f"mandelbrot-{count}.png", pad_inches=0)
        plt.close(fig2)  # Close the figure to free RAM.
        count += 1 # The next picture will be saved under the name "mandelbrot-2.png" and so on...
        fig.canvas.manager.set_window_title('The Mandelbrot Set')


if __name__ == '__main__':
    # Define the start values
    xmin, xmax = -2.5, 1.0
    ymin, ymax = -1.3125, 1.3125
    max_iter = 100
    count = 1

    # Compute the Mandelbrot set for the given start values
    mandelbrot_set = compute_mandelbrot(xmin, xmax, ymin, ymax)
    zmin = mandelbrot_set[mandelbrot_set > 0].min()
    zmax = mandelbrot_set.max()

    fig, ax = plt.subplots(figsize=(8, 6), dpi=180)         # 1440 x 1080 pixels at 180 DPI on a 8x6 inch canvas
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)   # The picture shall fill the whole canvas
    picture = ax.imshow(
        mandelbrot_set,
        extent=[xmin, xmax, ymin, ymax],
        cmap=mycolormap,
        norm=Normalize(vmin=zmin, vmax=zmax, clip=False),
        interpolation="none",
        origin="lower",
    )
    ax.set_axis_off()  # Do not show axes
    fig.canvas.manager.set_window_title('The Mandelbrot Set')

    # Handle events
    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect('key_press_event', on_key_press)

    # Show the plot
    plt.show()
