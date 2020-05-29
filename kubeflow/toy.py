from kfp import dsl
from kfp.components import InputPath, OutputPath, func_to_container_op


def trim(
    fastq: str,
    leading: int,
    trailing: int,
    minlen: int,
    sliding_window: str,
    trimmed_fastq: OutputPath("TrimmedFastq"),
) -> None:
    """
    In the function signature, `InputPath("Fastq")` is used to indicate a path to some
    fastq, and at runtime the actual path of the data gets passed. The `Fastq` argument
    is typechecked by the DSL compiler to make sure that types of data being passed from
    component to component match up.

    Because the trimmed fastq output path is controlled by Kubeflow, it does not have a
    .gz extension, and as such Trimmomatic thinks it's OK to not gzip the output file
    if we just pass that path directly. Instead, we pass a dummy filename to Trimmomatic
    and then just write the contents of that to the output path.
    """
    import os
    import subprocess

    subprocess.run(
        [
            "java",
            "-jar",
            "/software/Trimmomatic-0.38/trimmomatic-0.38.jar",
            "SE",
            "-phred33",
            fastq,
            "trimmed.fastq.gz",
            "LEADING:{}".format(leading),
            "TRAILING:{}".format(trailing),
            "SLIDINGWINDOW:{}".format(sliding_window),
            "MINLEN:{}".format(minlen),
        ],
        stderr=subprocess.STDOUT
    )

    os.rename("trimmed.fastq.gz", trimmed_fastq)


def plot(
    fastq: str,
    trimmed_fastq: InputPath("TrimmedFastq"),
    bar_color: str,
    flier_color: str,
    plot_color: str,
    plot: OutputPath("Plot")
) -> None:
    """
    This is a rather odd Pythonception. Don't do this in production! One of the nice
    things about the Kubeflow Pipelines SDK is that you can define your components
    in Python. Calling the script as a subprocess here is a legacy of the original WDL
    pipeline, WDL forces you to wrap all code with shell scripts. With KFP the compiler
    autogenerates CLI wrappers for you.

    Like in the trim task, tools often make unfortunate assumptions about the names of
    files. Here we pull a similar trick to get the plot to not complain due to the
    unexpected input filename.
    """
    import glob
    import os
    from shutil import copyfile
    import subprocess

    copyfile(trimmed_fastq, "trimmed.fastq.gz")

    subprocess.run(
        [
            "python3",
            "/software/demo-pipeline/src/plot_fastq_scores.py",
            "--untrimmed",
            fastq,
            "--trimmed",
            "trimmed.fastq.gz",
            "--bar-color",
            bar_color,
            "--flier-color",
            flier_color,
            "--plot-color",
            plot_color,
        ],
        stderr=subprocess.STDOUT
    )

    os.rename(glob.glob("*quality_scores.png")[0], plot)



trim_op = func_to_container_op(trim, base_image="quay.io/encode-dcc/demo-pipeline:template")
plot_op = func_to_container_op(plot, base_image="quay.io/encode-dcc/demo-pipeline:template")


@dsl.pipeline(
    name='ENCODE Demo Pipeline',
    description='A Kubeflow Pipelines implementation of the ENCODE DCC demo pipeline'
)
def demo_pipeline(
    fastqs=["/mnt/data/file1.fastq.gz", "/mnt/data/file2.fastq.gz"],
    leading: int = 5,
    trailing: int = 5,
    minlen: int = 80,
    sliding_window: str = "4:25",
    bar_color: str = "white",
    flier_color: str = "grey",
    plot_color: str = "darkgrid",
):
    """
    func_to_container_op simply converts the function into a factory that produces ops
    when called. add_pvolumes is a method of the op itself, so we need to apply it here
    when the op is actually generated, NOT above where the trim_op factory is created.
    """
    with dsl.ParallelFor(fastqs) as fastq:
        trim_task = trim_op(
            fastq=fastq,
            leading=leading,
            trailing=trailing,
            minlen=minlen,
            sliding_window=sliding_window,
        ).add_pvolumes({"/mnt/data": dsl.PipelineVolume(pvc="test-data-pv-claim")})

        _ = plot_op(
            fastq=fastq,
            trimmed_fastq=trim_task.outputs["trimmed_fastq"],
            bar_color=bar_color,
            flier_color=flier_color,
            plot_color=plot_color
        ).add_pvolumes({"/mnt/data": dsl.PipelineVolume(pvc="test-data-pv-claim")})
