---
comments: true
---

# Frequently Asked Questions

## Hardware

1) **Q:** Can this software run on a CPU cluster?

**A:** When I was developing the software, it turned out that the subtraction would be much faster using CUDA, so I chose to put most of the computational work on the GPUs. (Maybe it's a good idea to develop another CPU version of this software.) But for now, I don't think a CPU cluster will work. More CPUs just mean that more jobs will run in parallel and it takes more GPU memory. So I think more GPU memory would be better to accelerate this process because you can execute more jobs in the meantime.

2) **Q:** Memory leakage problems like:

> BrokenPipeError: [Errno 32] Broken pipe
> 
> multiprocessing/resource_tracker.py:216: UserWarning: resource_tracker: There appear to be 6 leaked semaphore objects to clean up at shutdown warnings.warn('resource_tracker: There appear to be %d '

**A:** This problem was probably due to memory leakage. You can try to use less cpus and smaller batch size. I’ve optimized the software so it should manage the GPU memory more properly. Please note that when you kill the process manually, it is possible that the BrokenPipeError may come up again but I think you can just skip that.

## Speed and Time

1) **Q:** How can I know the estimated time for the membrane subtraction, just like particle subtraction process in Relion?

**A:** Sorry, the estimated time is not accessible now. But you can refer to the prompts in the `run.out` file like "x / x minibatch finished" "xx particle stacks took xx seconds."

2) **Q:** How fast is the particle membrane subtraction?

**A:** When the software ran on a workstation which has 24 CPUs and one RTX4090 (24GB) using the default parameters, the speed was about 10 particles per second. (In this case, 18 CPUs were being used; the graphic card was almost full of memory; Volatile GPU-util was about 100%.)

3) **Q:** Will Micrograph Membrane Subtraction take a similarly long time as the Particle Membrane Subtraction?

**A:** Actually the time Micrograph Membrane Subtraction takes depends on the number of micrographs. When I tested this software using my own data, it took much less time than the particle membrane subtraction.

## Membrane Subtraction

1) **Q:** I used the default parameters in the membrane subtraction. I was wondering whether the membrane signal can be completely removed by changing some parameters.

**A:** Theoretically, the membrane can be completely removed using default parameters. You can check if the results of membrane analysis are as expected, like if the shapes of the membrane masks are reasonable for the corresponding 2D averages. If you find that everything is ok but the membrane signal is still not completely removed, you can set the **bias** in the Particles Membrane Subtraction interface. You can try to set the bias to 0.1.
!!! note
    a) if the bias is too high, the subtraction is likely to be excessive, and the gray value where the membrane signal exists may become negative.

    b) Removing the membrane completely is not best in all cases, and sometimes weakening the membrane signal would be a better option.

2) **Q:** If my job fails or suddenly stops, can I continue the membrane subtraction or do I need to restart it?

**A:** Yes, you can continue to do membrane subtraction if your job suddenly fails. The software will read the `run_data.log` file every time you begin to do membrane subtraction, and the finished particle stacks/micrographs in the `run_data.log` will be skipped. By the way, this software ran continuously for 6 days when I used it before and everything just went well.

3) **Q:** I was faced with a problem like this: `ValueError: Map ID string not found - not an MRC file, or file is corrupt` when doing Micrograph Membrane Subtraction. I'm sure that the micrographs should be fine.

**A:** It seems that it has something to do with the `mrcfile` python library when reading the micrographs. You can try to fix your micrographs by just using this command:

```bash

MemXTerminator fixmapid <path_to_mrc_file>
```

4) **Q:** When putting the membrane-subtracted particles back to micrograph, if two boxes overlap, how would it determine the value of the overlap region? That's say if there are two membranes in a particle, according to the 2D average, only one can be subtracted in the end; the other membrane may be picked in another particle.

**A:** Membrane-subtracted particles are weighted before putting back to the micrographs. So it turns out that the Micrograph Membrane Subtraction will combine information from multiple particles, even though there may be overlap between them. If there are two membranes in a particle, it's true that only one can be subtracted in the end; but as long as the other membrane has been picked and subtracted in another particle, when the software combines the info in these two particles, the two membranes will be subtracted in the micrograph eventually.

## Top view?

**Q:** The membrane subtraction can only remove the membrane signal from the side view. Can it also remove the membrane signal from the top view?

**A:** Good question. Actually I didn't take the top view into consideration and I have no idea how to localize and remove the membrane signal from the top view now. I think I need to find other ways out. But in practice, it seems that weakening or removing membrane signals from the side view is sufficient to reduce the effect of membrane signals on membrane proteins. We still need to try and test more.

## CTF estimation

**Q:** Can the membrane-subtracted micrographs directly do the CTF-estimation independently?

**A:** Theoretically, you can just take the subtracted micrographs as the raw micrographs, because all the other things are the same except the membrane signal, so I think it's okay to do the CTF estimation on the subtracted micrographs. I think it would be better to do CTF estimation before membrane subtraction.
