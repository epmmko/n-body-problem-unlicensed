# n-body-problem-unlicensed
Solving n-body problem and plotting it with Tkinter

### Resource used
* Nasa's planet/star location data
  * https://ssd.jpl.nasa.gov/horizons/app.html#/
* Kazam for video screen capture
* Kdenlive for speed-up the video to 10X
* Wikipedia for Equation dirvation
* Numpy/Scipy for solving Newton second law of motion
* Scipy for rotating view
* Tkinter for GUI
* regular expression for processing Nasa data
### Quick Program View


https://github.com/epmmko/n-body-problem-unlicensed/assets/26897526/ac0bc8bc-1192-47e2-9029-1a4ca8b382e8

# Full Description
```
"""Author: Ekarit Panacharoensawad
License: The Unlicensed (https://unlicense.org)
Version: 1.0.2024.05.05
Released date: May 5, 2024
Permanent download link: https://github.com/epmmko/n-body-problem-unlicensed
Description: This software provides the calculation of position and velocity 
    for two or more objects based on Newton's second law of motion 
    (n-body problem). The calculation is adjusting automatically
    as the number of objects is changed. More objects lead to slow calculation.
Limitation: This calculation does not account for any collision.
    The objects' velocity should be a lot less than the speed of light.
    If two objects are at the exact same position, the gravitational force 
    between object becomes infinity, and the answer to the equation of motion 
    at the next time step cannot be calculated.
Comparison with existing software: Even though this code was written by myself, 
    this n-body problem is a classic physics problem that already has multiple
    solution out there on the internet. Some of them even consider collision 
    (https://www.aanda.org/articles/aa/full_html/
     2012/01/aa18085-11/aa18085-11.html, 
     https://github.com/hannorein/rebound/, GPL-3.0 license).
    Some of them uses GPU and can run galaxy level simulation 
    (https://github.com/Hsin-Hung/N-body-simulation, Apache-2.0 license). 
    This software does not use GPU, cannot handle galaxy level simulation. 
    In fact, if we have about 5+ objects, the simulation will get quite slow.
    It does not have the correction to the numerical error as it run as other 
    approaches may have 
    (e.g. https://engineering.purdue.edu/people/kathleen.howell.1/
     Publications/Journals/2006_JSR_MarHowWil.pdf). 
    We will see that if we use symmetric initial condition, eventually the 
    objects' trajectories become asymmetric. Nevertheless, this software uses
    "The Unlicense" which means no conditions apply. The unlicensed works can 
    be distributed without source code and under different terms.
Possible usage: It can serve as
    *An easy example on how to solve the second law of motion.
    *An example on how to connect numerical result with GUI
    *An example on using the second thread to not freeze GUI while running
        * The zoom-in/out option is working while running the program
    *Teaching material for physics law implementation
        *For students in numerical method class (sophomore or junior year 
            for physics/math/computer science students
        *For students in math and science class 
            (K-12, depending on the depth that you want to do)
    *For me, the main audience is my daughters. It is for them to to see how 
    objects move.
        I do not really go into the coding or calculation parts. 
        I also use this code as a cheat sheet for Tk library.
    *...and of course, it can be used for fun. 
        It’s kinda cool to see how things move!
For the serious usage: This program can serve as an example on
        1) how to solve n-body problem with the number of object to be defined 
            at the run-time
        2) how to render it on the screen with the use of free libraries
    The default setting is based on the solar system coordinate from Nasa 
        on the time of 2460323.500000000 = A.D. 2024-Jan-14 00:00:00.0000 TDB 
        (Barycentric Dynamical Tim). This means it can be used to calculate 
        the realistic location of planets relative to the sun if the correct
        information is provided. The numerical method used is 
        Dormand & Prince (4)5 order with the relative tolerance of 1e-8. 
        This should allow somewhat accurate calculation of the real system.
Comments:
    *Coding part
        *Each window should be created as a separate canvas.
        *There should be a function to add a circle or an "x" mark on the 
            the screen (not to combine them together)
        *The mouse wheel for scrolling the scroll bar of the about text is 
            restricted to X11 machine.
            Platform independent GUI should be considered'
        *Add tooltip for all widgets.
    *Functionality
        *It would be nice to see the recent object path. 
            This may be added as a line behind the object
        *The object with higher mass should be larger
        *The circle edge of the object should change color depending on 
            the object's speed.
        *The ability to move the object in canvas then update the xyz 
            coordinate should be added
        *The ability to adjust the object velocity by double-clicking 
            the object and assign the velocity is nice to have
    *Major modification
        *Use javascript and make similar GUI/calculation, 
            then serves it on a website.
        *Make it more kids-friendly such that kindergarten students can use
            (may need to do the tablet version)
Acknowledgment: The author would like to thank physicists, mathematicians, 
    engineers, computer scientists, programmers, the open-source movement, 
    his teachers, and all related persons for the development of the equation
    of motion, the development of the numerical method for solving the 
    equation of motions, the development of hardware, software, the internet
    including but not limiting to the libraries used in this source code, 
    the programming language itself, the Linux OS that the author is using 
    for free, and free-websites that the author used for equation of motion 
    theory (wikipedia.org), developing the GUI (tkdocs), debugging the program
    (stackoverflow.com), and distribute this work (github.com). The author is 
    merely the person who used the existing laws of physics, mathematical and 
    computational knowledge together with the existing python libraries to do 
    the relevant calculations and generating the results. Last but not least, 
    he would like to thank his friend and family for continuous support during
    his entire life.
Request: If you find that this program, source code, or the trick to solve the
    second law of motion for any number of objects programmatically is useful, 
    please try to find a way to contribute (maybe, donating some money to 
    Unicef). Thank you for your consideration.
"""
```
