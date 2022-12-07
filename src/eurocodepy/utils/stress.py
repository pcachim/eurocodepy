import numpy as np
import math


def principals(sigxx: float, sigyy: float, sigzz: float, 
               sigxy: float, sigyz: float, sigzx: float) -> np.ndarray:
     """Calculate the principal stresses and the normalized principal directions
     Author. Paulo Cachim (2022)

     Args:
          sigxx (float): stress xx
          sigyy (float): stress yy
          sigzz (float): stress zz
          sigxy (float): stress xy
          sigyz (float): stress yz
          sigzx (float): stress zx

     Returns:
          ndarray, ndarray: the principal stresses and the normalized principal directions
     """
     return np.linalg.eigh(np.array([[sigxx,sigxy,sigzx],
                         [sigxy,sigyy,sigyz],
                         [sigzx,sigyz,sigzz]]))


def principal_vectors(sigxx: float, sigyy: float, sigzz: float, 
               sigxy: float, sigyz: float, sigzx: float) -> np.ndarray:
     """Calculates the princcipal vectors (size proportional to principal stresses)
     Author. Paulo Cachim (2022)

     Args:
          sigxx (float): stress xx
          sigyy (float): stress yy
          sigzz (float): stress zz
          sigxy (float): stress xy
          sigyz (float): stress yz
          sigzx (float): stress zx

     Returns:
          ndarray: an array of the principal vectors
     """

     values, vectors = np.linalg.eigh(np.array([[sigxx,sigxy,sigzx],
                         [sigxy,sigyy,sigyz],
                         [sigzx,sigyz,sigzz]]))

     v = vectors * np.array([values[0]*vectors[0], 
                    values[1]*vectors[1], 
                    values[2]*vectors[2]])
     return v


def invariants(sigxx: float, sigyy: float, sigzz: float, 
                         sigxy: float, sigyz: float, sigzx: float) -> list:
     """Calculates the stress invariants
     Author. Paulo Cachim (2022)

     Args:
          sigxx (float): stress xx
          sigyy (float): stress yy
          sigzz (float): stress zz
          sigxy (float): stress xy
          sigyz (float): stress yz
          sigzx (float): stress zx

     Returns:
          stress invariants (list): I1, J2, J3, mean_stress, eqv_stress, 
                         lode_r, lode_z, lode_theta, cos3t, triaxiality
     """
     #stresses = [0.0,0.0,0.0,0.0,0.0,0.0]

     # load the stresses into our matrix and compute the 
     # deviatoric and isotropic stress matricies
     sigma = np.array([[sigxx,sigxy,sigzx],
                         [sigxy,sigyy,sigyz],
                         [sigzx,sigyz,sigzz]])
     sigma_iso = (np.trace(sigma)*np.eye(3))/3.0
     sigma_dev = sigma - sigma_iso

     # # compute max shear stress
     # maxshear = (max(eigvals)-min(eigvals))/2.0

     # compute the stress invariants
     I1 = np.trace(sigma)
     J2 = 0.5*np.trace(np.dot(sigma_dev,sigma_dev))
     J3 = 0.333333333333333333*np.trace(np.dot(sigma_dev,np.dot(sigma_dev,sigma_dev)))

     # compute other common stress measures
     mean_stress = I1/3.0
     eqv_stress  = math.sqrt(3.0*J2)

     # compute lode coordinates
     lode_r = math.sqrt(2.0*J2)
     lode_z = I1/math.sqrt(3.0)

     stresses = 3.0*math.sqrt(6.0)*np.linalg.det(sigma_dev/lode_r)
     if stresses < -1: stresses = -1
     if stresses > 1: stresses = 1
     lode_theta = 1.0/3.0*math.asin(stresses)
     cos3t = 2.5980762114*J3/(J2**1.5)

     # compute the stress triaxiality
     triaxiality = mean_stress/eqv_stress
     
     return I1, J2, J3, mean_stress, eqv_stress, lode_r, lode_z, lode_theta, cos3t, triaxiality


if __name__ == "__main__":
     print("\nTest stress module: principals:")
     eval, evec = principals(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
     print(eval)
     print(evec)
     print("\nTest stress module: principal_vectors:")
     evec = principal_vectors(3.0, 2.0, -1.0, 0.0, 0.0, 0.0)
     print(evec)
     
     print("\nTest stress module: stress invariants:")
     u = invariants(3.0, 2.0, -1.0, 0.3, -0.4, 0.5)
     print (u)