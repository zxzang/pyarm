#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2010 Jérémie DECOCK (http://www.jdhp.org)

import sys
import os
import shutil
import getopt
import time
from pyarm import fig

INIT_TIME = time.time()   # Initial time (s)

def usage():
    """Print help message"""

    print '''Usage : ./pyarm [-m MUSCLE] [-a ARM] [-A AGENT] [-g GUI] [-r]
                [-d DELTA_TIME] [-s] [-l]
    
    A robotic arm model and simulator.

    -m, --muscle
        the muscle model to use (kambara, mitrovic, li or none)

    -a, --arm
        the arm model to use (kambara, mitrovic, li or sagittal)

    -A, --agent
        the agent to use (oscillator, random, filereader, sigmoid, heaviside,
        ilqg, none)

    -g, --gui
        the graphical user interface to use (tk, none)

    -r, --realtime
        realtime simulation (framerate dependant simulation) [default]

    -d, --deltatime
        timestep value in second (cancel -r option)
        should be near to 0.005 seconds

    -s, --screencast
        make a screencast

    -f, --figures
        save matplotlib figures

    -l, --log
        save numeric values (accelerations, velocities, angles, ...) into a
        file

    -u, --unbounded
        set unbounded joint angles

    -v, --version
        output version information and exit

    -h, --help
        display this help and exit
    '''


def main():
    """The main function.
    
    The purpose of this function is to get the list of modules to load and
    launch the simulator."""

    # Parse options ###########################################################
    muscle = 'none'
    arm = 'li'
    agent = 'none'
    gui = 'tk'
    realtime = True
    delta_time = None
    screencast = False
    save_figures = False
    log = False
    unbounded = False

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                     'm:a:A:g:rd:sfluvh',
                     ["muscle=", "arm=", "agent=", "gui=", "realtime",
                      "deltatime=", "screencast", "figures", "log",
                      "unbounded", "version", "help"])
    except getopt.GetoptError, err:
        # will print something like "option -x not recognized"
        print str(err) 
        usage()
        sys.exit(1)
 
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-m", "--muscle"):
            muscle = a
        elif o in ("-a", "--arm"):
            arm = a
        elif o in ("-A", "--agent"):
            agent = a
        elif o in ("-g", "--gui"):
            gui = a
        elif o in ("-r", "--realtime"):
            #realtime = True
            pass
        elif o in ("-d", "--deltatime"):
            delta_time = float(a)
            fig.DELTA_TIME = float(a)
            realtime = False
        elif o in ("-s", "--screencast"):
            screencast = True
            raise NotImplementedError()
        elif o in ("-f", "--figures"):
            save_figures = True
        elif o in ("-l", "--log"):
            log = True
        elif o in ("-u", "--unbounded"):
            unbounded = True
        elif o in ("-v", "--version"):
            # TODO
            sys.exit(0)
        else:
            assert False, "unhandled option"

    if muscle not in ('none', 'kambara', 'mitrovic', 'li') \
        or arm not in ('kambara', 'mitrovic', 'li', 'sagittal') \
        or agent not in ('none', 'oscillator', 'random', 'filereader',
                         'sigmoid', 'heaviside', 'ilqg') \
        or gui not in ('tk', 'gtk', 'cairo', 'none'):
        usage()
        sys.exit(2)

    # Init ####################################################################

    if muscle == 'none':
        from pyarm.model.muscle import fake_muscle_model as muscle_module
    elif muscle == 'kambara':
        from pyarm.model.muscle import kambara_muscle_model as muscle_module
    elif muscle == 'mitrovic':
        from pyarm.model.muscle import mitrovic_muscle_model as muscle_module
    elif muscle == 'li':
        from pyarm.model.muscle import weiwei_muscle_model as muscle_module
    else:
        usage()
        sys.exit(2)

    if arm == 'kambara':
        from pyarm.model.arm import kambara_arm_model as arm_module
    elif arm == 'mitrovic':
        from pyarm.model.arm import mitrovic_arm_model as arm_module
    elif arm == 'li':
        from pyarm.model.arm import weiwei_arm_model as arm_module
    elif arm == 'sagittal':
        from pyarm.model.arm import sagittal_arm_model as arm_module
    else:
        usage()
        sys.exit(2)

    if agent == 'none':
        agent_module = None
        print 'Press NumKey 1 to 6 to move the arm'
    elif agent == 'oscillator':
        from pyarm.agent import oscillator as agent_module
    elif agent == 'random':
        from pyarm.agent import random_oscillator as agent_module
    elif agent == 'filereader':
        from pyarm.agent import filereader as agent_module
    elif agent == 'sigmoid':
        from pyarm.agent import sigmoid as agent_module
    elif agent == 'heaviside':
        from pyarm.agent import heaviside as agent_module
    elif agent == 'ilqg':
        if muscle == 'none':
            from pyarm.agent import ilqg_agent as agent_module
            if delta_time is None:
                print("ILQG agent can't be used in realtime mode. " + \
                      "Use -d option to set a delta_time value.")
                sys.exit(3)
            else:
                agent_module.DELTA_TIME = delta_time
        else:
            from pyarm.agent import ilqg6_agent as agent_module
            if delta_time is None:
                print("ILQG agent can't be used in realtime mode. " + \
                      "Use -d option to set a delta_time value.")
                sys.exit(3)
            else:
                agent_module.DELTA_TIME = delta_time
    else:
        usage()
        sys.exit(2)

    if gui == 'tk':
        from pyarm.gui import tkinter_gui as gui_mod
    elif gui == 'gtk':
        raise NotImplementedError()
    elif gui == 'cairo':
        raise NotImplementedError()
    elif gui == 'none':
        raise NotImplementedError()
    else:
        usage()
        sys.exit(2)

    arm = arm_module.ArmModel(unbounded)
    muscle = muscle_module.MuscleModel()

    agent = None
    if agent_module != None:
        agent = agent_module.Agent()

    gui = gui_mod.GUI(muscle, arm)

    # Erase the screencast directory
    if screencast:
        shutil.rmtree('screencast', True)
        os.mkdir('screencast')

    # The mainloop ############################################################
    fig.subfig('dtime', title='Time', xlabel='time (s)', ylabel='Delta time (s)')
    former_time = INIT_TIME

    while gui.running:

        # Compute delta time
        current_time = time.time()

        if realtime:
            delta_time = current_time - former_time
    
        fig.append('dtime', delta_time)

        # Get input signals
        commands = None
        if agent == None:
            commands = [float(flag) for flag in gui.keyboard_flags]
        else:
            elapsed_time = current_time - INIT_TIME
            commands = agent.get_commands(arm.angles,
                                          arm.velocities,
                                          elapsed_time)
    
        # Update angles (physics)
        torque = muscle.compute_torque(arm.angles, arm.velocities, commands)
        acceleration = arm.compute_acceleration(torque, delta_time)

        # Update clock
        former_time = current_time

        gui.update(commands, torque, acceleration)

    # Quit ####################################################################
    if screencast:
        print "Making screencast..."
        os.system("ffmpeg2theora -f image2 %(path)s/%%05d.jpeg" + \
                  "-o %(path)s/screencast.ogv" % {'path': 'screencast'})

    if log:
        print 'Saving log...'
        fig.save_log()

    # Display figures
    if save_figures:
        print 'Saving figures...'
        fig.save_all_figs()
    fig.show()

if __name__ == '__main__':
    main()
    #parse_arguments()
    #init()
    #run()
    #finalize()

