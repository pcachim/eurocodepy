# EurocodePy

Here are some guide questions that will help you out:

What was your motivation? \
Why did you build this project? \
What problem does it solve? \
What did you learn? \
What makes your project stand out? \
If your project has a lot of features, consider adding a "Features" section and listing them here.

What your application does, \
Why you used the technologies you used, \
Some of the challenges you faced and features you hope to implement in the future.

### Calculate the resistance of a concrete section according to Eurocode 2

resistance = ec2.concrete_section_resistance(fck=30, b=0.2, h=0.4, d=0.35, fyk=500)

### Calculate the shear capacity of a reinforced concrete beam according to Eurocode 2

shear_capacity = ec2.shear_capacity_beam(b=0.3, d=0.4, as_=0.01, fck=30, fyk=500, vEd=50)

### Calculate the bending moment capacity of a reinforced concrete beam according to Eurocode 2

moment_capacity = ec2.bending_moment_capacity_beam(b=0.3, d=0.4, as_=0.01, fck=30, fyk=500)
In addition to the Eurocode 2 functions shown above, EurocodePy includes functions for Eurocodes 0, 1, 3, 4, 5, 6, 7, 8, 9, and EN 1992-1-1.

### Create a material object for concrete

concrete = Material(name="C30/37", fck=30, fck_cube=37, fctm=2.6, Ecm=31000, G=11500)

### Create a material object for steel

steel = Material(name="S500", fyk=500, fuk=630, E=200000, G=77000)

### Use the concrete object in a Eurocode 2 calculation

resistance = ec2.concrete_section_resistance(b=0.2, h=0.4, d=0.35, material=concrete, gamma_c=1.5)

### Use the steel object in a Eurocode 3 calculation

section_class = ec3.section_classification(h=0.3, b=0.2, t=0.01, material=steel)
