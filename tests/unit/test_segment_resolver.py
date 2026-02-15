from src.domain.segment_resolver import (
    resolve_segment_ref,
    get_segment_root,
    get_segment_slug,
    get_segment_fingerprint,
    get_segment_id,
)


class TestSegmentRef:
    def test_resolve_current_directory(self):
        ref = resolve_segment_ref(".")
        assert ref.slug == "wo-0042"
        assert len(ref.fingerprint) == 8
        assert ref.id == f"{ref.slug}_{ref.fingerprint}"
        assert ref.root_abs.is_absolute()

    def test_resolve_absolute_path(self, tmp_path):
        test_dir = tmp_path / "my-test-project"
        test_dir.mkdir()
        ref = resolve_segment_ref(test_dir)
        assert ref.slug == "my-test-project"
        assert len(ref.fingerprint) == 8
        assert ref.root_abs == test_dir.resolve()

    def test_segment_slug_normalization(self, tmp_path):
        test_dir = tmp_path / "My Test@Project!"
        test_dir.mkdir()
        ref = resolve_segment_ref(test_dir)
        assert ref.slug == "my-test_project_"

    def test_different_paths_same_name_different_fingerprint(self, tmp_path):
        dir1 = tmp_path / "project"
        dir2 = tmp_path / "other" / "project"
        dir1.mkdir(parents=True)
        dir2.mkdir(parents=True)

        ref1 = resolve_segment_ref(dir1)
        ref2 = resolve_segment_ref(dir2)

        assert ref1.slug == ref2.slug == "project"
        assert ref1.fingerprint != ref2.fingerprint
        assert ref1.id != ref2.id

    def test_fingerprint_is_deterministic(self, tmp_path):
        test_dir = tmp_path / "deterministic-test"
        test_dir.mkdir()

        ref1 = resolve_segment_ref(test_dir)
        ref2 = resolve_segment_ref(test_dir)

        assert ref1.fingerprint == ref2.fingerprint
        assert ref1.id == ref2.id

    def test_custom_hash_length(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()

        ref8 = resolve_segment_ref(test_dir, hash_length=8)
        ref12 = resolve_segment_ref(test_dir, hash_length=12)

        assert len(ref8.fingerprint) == 8
        assert len(ref12.fingerprint) == 12
        assert ref8.fingerprint == ref12.fingerprint[:8]

    def test_segment_id_format(self, tmp_path):
        test_dir = tmp_path / "my-project"
        test_dir.mkdir()
        ref = resolve_segment_ref(test_dir)
        assert ref.id == f"{ref.slug}_{ref.fingerprint}"
        assert "_" in ref.id

    def test_root_abs_is_canonical(self, tmp_path):
        test_dir = tmp_path / "canonical-test"
        test_dir.mkdir()
        ref = resolve_segment_ref(test_dir)
        assert ref.root_abs == ref.root_abs.resolve()

    def test_none_input_uses_cwd(self):
        import os

        original_cwd = os.getcwd()
        try:
            ref_none = resolve_segment_ref(None)
            ref_dot = resolve_segment_ref(".")
            assert ref_none.root_abs == ref_dot.root_abs
            assert ref_none.id == ref_dot.id
        finally:
            os.chdir(original_cwd)


class TestConvenienceFunctions:
    def test_get_segment_root(self, tmp_path):
        test_dir = tmp_path / "test-root"
        test_dir.mkdir()
        root = get_segment_root(test_dir)
        assert root == test_dir.resolve()

    def test_get_segment_slug(self, tmp_path):
        test_dir = tmp_path / "My-Test"
        test_dir.mkdir()
        slug = get_segment_slug(test_dir)
        assert slug == "my-test"

    def test_get_segment_fingerprint(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        fp = get_segment_fingerprint(test_dir)
        assert len(fp) == 8

    def test_get_segment_id(self, tmp_path):
        test_dir = tmp_path / "test-id"
        test_dir.mkdir()
        sid = get_segment_id(test_dir)
        assert "_" in sid
        assert len(sid) > 8


class TestCanonicalization:
    def test_expanduser(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        ref = resolve_segment_ref(str(test_dir))
        assert "~" not in str(ref.root_abs)

    def test_resolve_makes_absolute(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        ref = resolve_segment_ref(test_dir)
        assert ref.root_abs.is_absolute()


class TestSegmentRefEquality:
    def test_same_path_equals(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        ref1 = resolve_segment_ref(test_dir)
        ref2 = resolve_segment_ref(test_dir)
        assert ref1 == ref2

    def test_different_path_not_equals(self, tmp_path):
        dir1 = tmp_path / "test1"
        dir2 = tmp_path / "test2"
        dir1.mkdir()
        dir2.mkdir()
        ref1 = resolve_segment_ref(dir1)
        ref2 = resolve_segment_ref(dir2)
        assert ref1 != ref2

    def test_hashable(self, tmp_path):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        ref = resolve_segment_ref(test_dir)
        s = {ref}
        assert ref in s
