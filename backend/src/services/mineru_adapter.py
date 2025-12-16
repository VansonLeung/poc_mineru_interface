from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, TYPE_CHECKING

from loguru import logger

from src.config.settings import get_settings

if TYPE_CHECKING:
    from mineru.data.data_reader_writer import FileBasedDataWriter


@dataclass
class MineruOutputPaths:
    filename: str
    markdown: Optional[Path]
    content_list: Optional[Path]
    middle_json: Optional[Path]
    model_output: Optional[Path]
    image_dir: Optional[Path]


class MineruUnavailableError(RuntimeError):
    """Raised when Miner-U optional dependencies are not present."""


class MineruAdapter:
    """Thin wrapper around Miner-U demo script to parse bytes and return output file paths."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        self.settings = get_settings()
        # Ensure Miner-U respects configured model source
        if "MINERU_MODEL_SOURCE" not in os.environ and self.settings.mineru_model_source:
            os.environ["MINERU_MODEL_SOURCE"] = self.settings.mineru_model_source

        self.output_dir = Path(output_dir or self.settings.output_base_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_from_paths(
        self,
        paths: Iterable[Path],
        lang: str = "ch",
        backend: str = "pipeline",
        parse_method: str = "auto",
        server_url: Optional[str] = None,
        start_page: int = 0,
        end_page: Optional[int] = None,
        formula_enable: bool = True,
        table_enable: bool = True,
    ) -> List[MineruOutputPaths]:
        from mineru.cli.common import read_fn
        from mineru.utils.guess_suffix_or_lang import guess_suffix_by_path

        file_bytes: list[bytes] = []
        file_names: list[str] = []
        lang_list: list[str] = []
        for path in paths:
            file_names.append(Path(path).stem)
            file_bytes.append(read_fn(path))
            lang_list.append(lang)
        return self.parse_from_bytes(
            list(zip(file_names, file_bytes)),
            lang=lang_list,
            backend=backend,
            parse_method=parse_method,
            server_url=server_url,
            start_page=start_page,
            end_page=end_page,
            formula_enable=formula_enable,
            table_enable=table_enable,
        )

    def parse_from_bytes(
        self,
        files: list[tuple[str, bytes]],
        lang: str | list[str] = "ch",
        backend: str = "pipeline",
        parse_method: str = "auto",
        server_url: Optional[str] = None,
        start_page: int = 0,
        end_page: Optional[int] = None,
        formula_enable: bool = True,
        table_enable: bool = True,
    ) -> List[MineruOutputPaths]:
        try:
            from mineru.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2, prepare_env
            from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
            from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
            from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
            from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
            from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
            from mineru.data.data_reader_writer import FileBasedDataWriter
            from mineru.utils.enum_class import MakeMode
        except ImportError as exc:  # torch or other heavy deps missing
            raise MineruUnavailableError(f"Miner-U dependencies are not installed: {exc}") from exc

        file_names = [name for name, _ in files]
        pdf_bytes_list = [data for _, data in files]
        lang_list = [lang] * len(files) if isinstance(lang, str) else lang

        outputs: list[MineruOutputPaths] = []

        if backend == "pipeline":
            for idx, pdf_bytes in enumerate(pdf_bytes_list):
                pdf_bytes_list[idx] = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page, end_page)

            infer_results, all_image_lists, all_pdf_docs, detected_langs, ocr_enabled_list = pipeline_doc_analyze(
                pdf_bytes_list,
                lang_list,
                parse_method=parse_method,
                formula_enable=formula_enable,
                table_enable=table_enable,
            )

            for idx, model_list in enumerate(infer_results):
                model_json = copy.deepcopy(model_list)
                filename = file_names[idx]
                local_image_dir, local_md_dir = prepare_env(self.output_dir, filename, parse_method)
                image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)

                images_list = all_image_lists[idx]
                pdf_doc = all_pdf_docs[idx]
                _lang = detected_langs[idx]
                _ocr_enable = ocr_enabled_list[idx]
                middle_json = pipeline_result_to_middle_json(
                    model_list,
                    images_list,
                    pdf_doc,
                    image_writer,
                    _lang,
                    _ocr_enable,
                    formula_enable,
                )

                pdf_info = middle_json["pdf_info"]
                output_paths = self._process_output(
                    pdf_info=pdf_info,
                    pdf_bytes=pdf_bytes_list[idx],
                    filename=filename,
                    local_md_dir=local_md_dir,
                    image_dir=local_image_dir,
                    writer=md_writer,
                    is_pipeline=True,
                    middle_json=middle_json,
                    model_output=model_json,
                )
                outputs.append(output_paths)
        else:
            backend_name = backend[4:] if backend.startswith("vlm-") else backend
            parse_method = "vlm"
            # Fail fast when local model source is selected but config is missing
            if os.getenv("MINERU_MODEL_SOURCE", "") == "local":
                try:
                    from mineru.utils.config_reader import get_local_models_dir

                    models_dir = get_local_models_dir()
                    if not models_dir or not isinstance(models_dir, dict) or "vlm" not in models_dir:
                        raise MineruUnavailableError(
                            "MINERU_MODEL_SOURCE=local requires ~/mineru.json with models-dir.vlm path configured",
                        )
                except MineruUnavailableError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    raise MineruUnavailableError(
                        "Failed to read Miner-U local model config for VLM backend",
                    ) from exc

            for idx, pdf_bytes in enumerate(pdf_bytes_list):
                filename = file_names[idx]
                pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page, end_page)
                local_image_dir, local_md_dir = prepare_env(self.output_dir, filename, parse_method)
                image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
                middle_json, infer_result = vlm_doc_analyze(
                    pdf_bytes,
                    image_writer=image_writer,
                    backend=backend_name,
                    server_url=server_url,
                )

                pdf_info = middle_json["pdf_info"]
                output_paths = self._process_output(
                    pdf_info=pdf_info,
                    pdf_bytes=pdf_bytes,
                    filename=filename,
                    local_md_dir=local_md_dir,
                    image_dir=local_image_dir,
                    writer=md_writer,
                    is_pipeline=False,
                    middle_json=middle_json,
                    model_output=infer_result,
                )
                outputs.append(output_paths)

        return outputs

    def _process_output(
        self,
        pdf_info,
        pdf_bytes,
        filename: str,
        local_md_dir: str | Path,
        image_dir: str | Path,
        writer,
        is_pipeline: bool,
        middle_json,
        model_output=None,
    ) -> MineruOutputPaths:
        from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
        from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
        from mineru.utils.enum_class import MakeMode

        local_md_dir = Path(local_md_dir)
        image_dir = Path(image_dir)

        markdown_path = None
        content_list_path = None
        middle_json_path = None
        model_output_path = None

        make_func = pipeline_union_make if is_pipeline else vlm_union_make
        md_content_str = make_func(pdf_info, MakeMode.MM_MD, image_dir.name)
        markdown_path = local_md_dir / f"{filename}.md"
        writer.write_string(markdown_path.name, md_content_str)

        content_list = make_func(pdf_info, MakeMode.CONTENT_LIST, image_dir.name)
        content_list_path = local_md_dir / f"{filename}_content_list.json"
        writer.write_string(content_list_path.name, json.dumps(content_list, ensure_ascii=False, indent=2))

        middle_json_path = local_md_dir / f"{filename}_middle.json"
        writer.write_string(middle_json_path.name, json.dumps(middle_json, ensure_ascii=False, indent=2))

        if model_output is not None:
            model_output_path = local_md_dir / f"{filename}_model.json"
            writer.write_string(model_output_path.name, json.dumps(model_output, ensure_ascii=False, indent=2))

        logger.info(f"local output dir is {local_md_dir}")
        return MineruOutputPaths(
            filename=filename,
            markdown=markdown_path,
            content_list=content_list_path,
            middle_json=middle_json_path,
            model_output=model_output_path,
            image_dir=image_dir,
        )


def guess_input_files(input_dir: Path) -> list[Path]:
    pdf_suffixes = ["pdf"]
    image_suffixes = ["png", "jpeg", "jp2", "webp", "gif", "bmp", "jpg"]
    paths: list[Path] = []
    for doc_path in input_dir.glob("*"):
        if guess_suffix_by_path(doc_path) in pdf_suffixes + image_suffixes:
            paths.append(doc_path)
    return paths
