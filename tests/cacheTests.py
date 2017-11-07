import unittest
from app.openStreetMap import Cache
import os
import shutil


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.cache = Cache()

    def testCheckExistFolder(self):
        self.assertTrue(self.cache.exist())

    def testCreateSubfolder1(self):
        if self.cache.exist(['test']):
            shutil.rmtree(os.path.join(self.cache.cache_dir, 'test'))
        self.assertFalse(self.cache.exist(['test']))
        self.cache.create_subfolder(['test'])
        self.assertTrue(self.cache.exist(['test']))
        shutil.rmtree(os.path.join(self.cache.cache_dir, 'test'))

    def testCreateSubfolder2(self):
        if self.cache.exist(['test']):
            shutil.rmtree(os.path.join(self.cache.cache_dir, 'test'))
        self.assertFalse(self.cache.exist(['test']))
        self.cache.create_subfolder(['test', 'test111'])
        self.assertTrue(self.cache.exist(['test', 'test111']))
        shutil.rmtree(os.path.join(self.cache.cache_dir, 'test'))
