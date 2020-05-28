from kfp import dsl
from kfp.components import InputPath, OutputPath, func_to_container_op


def trim(
    fastq: InputPath("Fastq"),
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
    """
    import subprocess

    subprocess.run(
        [
            "java",
            "-jar",
            "/software/Trimmomatic-0.38/trimmomatic-0.38.jar",
            "SE",
            "-phred33",
            fastq,
            trimmed_fastq,
            "LEADING:{}".format(leading),
            "TRAILING:{}".format(trailing),
            "SLIDINGWINDOW:{}".format(sliding_window),
            "MINLEN:{}".format(minlen),
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


def plot(
    fastq: InputPath("Fastq"),
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
    pipeline, WDL forces you to wrap all code with shell scripts.
    """
    import subprocess

    subprocess.run(
        [
            "python3 /software/demo-pipeline/src/plot_fastq_scores.py",
            "--untrimmed {}".format(fastq),
            "--trimmed {}".format(trimmed_fastq),
            "--bar-color {}".format(bar_color),
            "--flier-color {}".format(flier_color),
            "--plot-color {}".format(plot_color),
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


trim_op = func_to_container_op(trim, base_image="quay.io/encode-dcc/demo-pipeline:template")
plot_op = func_to_container_op(plot, base_image="quay.io/encode-dcc/demo-pipeline:template")


@dsl.pipeline(
    name='ENCODE Demo Pipeline',
    description='A Kubeflow Pipelines implementation of the ENCODE DCC demo pipeline'
)
def demo_pipeline(
    fastqs=["minio://data/file1.fastq.gz", "minio://data/file2.fastq.gz"],
    leading: int = 5,
    trailing: int = 5,
    minlen: int = 80,
    sliding_window: str = "4:25",
    bar_color: str = "white",
    flier_color: str = "grey",
    plot_color: str = "darkgrid",
):
    with dsl.ParallelFor(fastqs) as fastq:
        trim_task = trim_op(
            fastq=fastq,
            leading=leading,
            trailing=trailing,
            minlen=minlen,
            sliding_window=sliding_window,
        )

        _ = plot_op(
            fastq=fastq,
            trimmed_fastq=trim_task.outputs["trimmed_fastq"],
            bar_color=bar_color,
            flier_color=flier_color,
            plot_color=plot_color
        )
