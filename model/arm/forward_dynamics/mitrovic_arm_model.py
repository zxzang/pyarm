# -*- coding: utf-8 -*-

# Copyright (c) 2010 Jérémie DECOCK (http://www.jdhp.org)

from abstract_arm_model import AbstractArmModel
from kinematics import euler as kinematics
import math
import numpy as np
import fig

class ArmModel(AbstractArmModel):
    """Horizontally planar 2 DoF arm model.
    
    References :

    Djordje Mitrovic
    http://www.ipab.informatics.ed.ac.uk/slmc/SLMCpeople/Mitrovic_D.html

    [1] Djordje Mitrovic, Stefan Klanke, and Sethu Vijayakumar,
    "Adaptive Optimal Control for Redundantly Actuated Arms",
    Proc. Simulation of Adaptive Behavior (SAB), 2008
    
    [2] Djordje Mitrovic, Stefan Klanke, and Sethu Vijayakumar,
    "Optimal Control with Adaptive Internal Dynamics Models",
    Proc. International Conference on Informatics in Control,
    Automation and Robotics (ICINCO), 2008

    [3] Djordje Mitrovic, Stefan Klanke, Rieko Osu, Mitsuo Kawato,
    and Sethu Vijayakumar, "Impedance Control as an Emergent Mechanism from
    Minimising Uncertainty", under review,  preprint, 2009

    [4] Djordje Mitrovic, Sho Nagashima, Stefan Klanke, Takamitsu Matsubara,
    and Sethu Vijayakumar, "Optimal Feedback Control for Anthropomorphic
    Manipulators", Accepted for ICRA, 2010

    [5] Djordje Mitrovic, Stefan Klanke, and Sethu Vijayakumar,
    "Exploiting Sensorimotor Stochasticity for Learning Control of Variable
    Impedance Actuators", under review, preprint available soon, 2010

    ---

    This model is based on [6] and [7]

    [6] M. Katayama and M. Kawato (1993), "Virtual trajectory and stiffness
    ellipse during multijoint arm movement predicted by neural inverse models".
    Biological Cybernetics, 69:353-362.

    [7] Todorov & Li
    """

    name = 'Mitrovic'

    legend = ('shoulder', 'elbow')

    # Arm parameters from from [6] p.356 ######################################

    shoulder_inertia = 4.77E-2   # Moment of inertia at shoulder join (kg·m²)
    elbow_inertia = 5.88E-2      # Moment of inertia at elbow join (kg·m²)

    forearm_mass = 1.44          # Forearm mass (kg)

    upperarm_length = 0.3        # Upperarm length (m)
    forearm_length = 0.35        # Upperarm length (m)

    # Distance from the forearm joint center to the forearm center of mass (m)
    forearm_cog = 0.21 


    def __init__(self):
        self.alpha = np.zeros(2)               # Angular acceleration (rd/s²)
        self.omega = np.zeros(2)               # Angular velocity (rd/s)
        self.theta = np.array(self.theta_init) # Joint angle (rd)

        self.bound_joint_angles()

        # Init datas to plot
        fig.subfig('alpha',
                   title='Angular acceleration',
                   xlabel='time (s)',
                   ylabel='Angular acceleration (rad/s/s)',
                   legend=self.legend)
        fig.subfig('omega',
                   title='Angular velocity',
                   xlabel='time (s)',
                   ylabel='Angular velocity (rad/s)',
                   legend=self.legend)
        fig.subfig('theta',
                   title='Angle',
                   xlabel='time (s)',
                   ylabel='Angle (rad)',
                   legend=self.legend)


    def update(self, tau, dt):
        "Compute the arm dynamics."

        # Angular acceleration ########
        M = self.M(self.theta)
        C = self.C(self.theta, self.omega)

        # from [1] p.3, [3] p.4 and [6] p.354
        self.alpha = np.dot(np.linalg.inv(M), tau - C) 

        fig.append('alpha', self.alpha)
        assert self.alpha.min() >= self.alphamin \
           and self.alpha.max() <= self.alphamax, "Angular acceleration %f" % self.alpha

        # Forward kinematics
        self.alpha, self.omega, self.theta = kinematics.forward_kinematics(acceleration=self.alpha,
                                                               velocity=self.omega,
                                                               angle=self.theta,
                                                               delta_time=dt)
        self.bound_joint_angles()

        fig.append('omega', self.omega)
        fig.append('theta', self.theta)

        assert self.omega.min() >= self.omegamin \
               and self.omega.max() <= self.omegamax, "Angular velocity %f" % self.omega

        return self.alpha.tolist(), self.omega.tolist(), self.theta.tolist()
