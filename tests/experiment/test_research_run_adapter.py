import tempfile
import unittest
from pathlib import Path
from remgu import Experiment, Motivation, ResearchRunAdapter, SimulationConfig, SimulationExperiment

class TestResearchRunAdapter(unittest.TestCase):
    def test_records_result_to_existing_running_run(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = Experiment('adapter-test', Path(directory) / '.research')
            with experiment.run('Test simulation integration', Motivation(type='new')) as run:
                result = SimulationExperiment(SimulationConfig(seed=1)).run()
                ResearchRunAdapter().record(run, result)
                self.assertTrue(run.params_path.exists())
                self.assertTrue(run.samples_path.exists())

    def test_rejects_finished_run(self):
        with tempfile.TemporaryDirectory() as directory:
            experiment = Experiment('adapter-test', Path(directory) / '.research')
            run = experiment.run('Test simulation integration', Motivation(type='new'))
            run.complete()
            result = SimulationExperiment(SimulationConfig(seed=1)).run()
            with self.assertRaises(RuntimeError):
                ResearchRunAdapter().record(run, result)
