from kfp import dsl
from kfp.components import InputPath, func_to_container_op


@func_to_container_op(base_image="quay.io/encode-dcc/demo-pipeline:template")
def trim(
    input_fastq: InputPath("Fastq"),
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
            "java -jar /software/Trimmomatic-0.38/trimmomatic-0.38.jar SE -phred33",
            input_fastq,
            trimmed_fastq,
            "LEADING:{}".format(leading),
            "TRAILING:{}".format(trailing),
            "SLIDINGWINDOW:{}".format(sliding_window),
            "MINLEN:{}".format(minlen),
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


@func_to_container_op(base_image="quay.io/encode-dcc/demo-pipeline:template")
def plot(
    fastq: InputPath("Fastq"),
    trimmed_fastq: InputPath("TrimmedFastq"),
    bar_color: int,
    flier_color: int,
    plot_color: int,
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


@dsl.pipeline(
    name='ENCODE Demo Pipeline',
    description='A Kubeflow Pipelines implementation of the ENCODE DCC demo pipeline'
)
def demo_pipeline(
    output,
    project,
    region='us-central1',
    train_data='gs://ml-pipeline-playground/sfpd/train.csv',
    eval_data='gs://ml-pipeline-playground/sfpd/eval.csv',
    schema='gs://ml-pipeline-playground/sfpd/schema.json',
    target='resolution',
    rounds=200,
    workers=2,
    true_label='ACTION',
):
    with dsl.ParallelFor([{"a": 1, "b": 10}, {"a": 2, "b": 20}]) as item:
        op1 = plot(…, args=["echo {}".format(item.a)])
