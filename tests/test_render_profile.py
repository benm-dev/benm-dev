"""Verify anonymity, attribution, arithmetic and geometry edge cases."""
import copy
import datetime as dt
import pathlib
import sys
import unittest
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import render_profile as renderer
from collect_activity import aggregate, validate


class RenderingInputs(unittest.TestCase):
    def setUp(self):
        self.now = dt.datetime(2026,9,11,12,tzinfo=dt.timezone.utc)
        self.days = [(self.now.date()-dt.timedelta(days=55-i)).isoformat() for i in range(56)]

    def snapshot(self, commits=(), openings=()):
        return aggregate(self.days, commits, openings, self.now.isoformat())

    def test_private_and_public_fork_duplicates_count_once_as_public(self):
        private = {'sha':'secret-id','day':self.days[-1],'visibility':'private','repo':'do-not-export','payload':'do-not-export'}
        public = dict(private,visibility='public')
        snapshot = self.snapshot([private,private,public])
        self.assertEqual(snapshot['records_total'],1)
        self.assertEqual(sum(snapshot['public_series']),1)
        self.assertEqual(sum(snapshot['private_series']),0)
        self.assertNotIn('secret-id',str(snapshot))
        self.assertNotIn('do-not-export',str(snapshot))

    def test_private_openings_are_counted_without_exporting_extra_fields(self):
        opening={'day':self.days[-2],'kind':'pull_requests','visibility':'private','title':'confidential'}
        snapshot=self.snapshot(openings=[opening])
        self.assertEqual(sum(snapshot['private_series']),1)
        self.assertNotIn('confidential',str(snapshot))

    def test_empty_sample_has_finite_mesh_and_unit_normals(self):
        mesh,normals,*_=renderer.geometry(self.snapshot())
        self.assertTrue(np.isfinite(mesh).all())
        np.testing.assert_allclose(np.linalg.norm(normals,axis=-1),1,atol=1e-10)

    def test_rotation_and_section_alignment_close_smoothly(self):
        snapshot=self.snapshot()
        np.testing.assert_allclose(renderer.rotation(0,snapshot['seed']),renderer.rotation(renderer.TAU,snapshot['seed']),atol=1e-12)
        mesh,*_=renderer.geometry(snapshot)
        radial=renderer.normalize(mesh-mesh.mean(axis=1)[:,None,:])
        self.assertGreater(float(np.sum(radial*np.roll(radial,-1,axis=0),axis=-1).min()),.95)

    def test_rejects_extra_fields_inconsistent_totals_and_missing_dates(self):
        base=self.snapshot()
        for key,value in [('repo','private-name'),('records_total',99)]:
            broken=copy.deepcopy(base);broken[key]=value
            with self.assertRaises(ValueError): validate(broken)
        broken=copy.deepcopy(base);broken['days'][3]=broken['days'][4]
        with self.assertRaises(ValueError): validate(broken)
        broken=copy.deepcopy(base);broken['series'][3]=-1
        with self.assertRaises(ValueError): validate(broken)


if __name__=='__main__': unittest.main()
