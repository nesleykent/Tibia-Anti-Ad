"""Start a pinned, CPU-only local teacher on an ephemeral Linux Actions runner."""
import hashlib
import json
import os
import subprocess
import time
import urllib.request

from tibia_learning import WORK, MODEL_NAME, LABELLER_URL, StageError, verify_labeller

VERSION = 'v0.40.10'
ARCHIVE_SHA256 = '1e8ad2d2a394efdd235bee74deec237badd95142ffba77588140ab2a9ecec227'
URL = f'https://github.com/ollama/ollama/releases/download/{VERSION}/ollama-linux-amd64.tar.zst'


def start():
    runtime = WORK / 'ollama-runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    archive = runtime / 'runtime.tar.zst'
    digest = hashlib.sha256()
    with urllib.request.urlopen(URL, timeout=90) as source, archive.open('wb') as dest:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
            dest.write(chunk)
    if digest.hexdigest() != ARCHIVE_SHA256:
        raise StageError('Local runtime checksum mismatch')
    subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(runtime)], check=True)
    archive.unlink()
    binary = runtime / 'bin/ollama'
    env = dict(os.environ, OLLAMA_HOST='127.0.0.1:11434', OLLAMA_NO_CLOUD='1',
               OLLAMA_MODELS=str(WORK / 'ollama-models'), CUDA_VISIBLE_DEVICES='-1',
               OLLAMA_NUM_PARALLEL='1', OLLAMA_MAX_LOADED_MODELS='1')
    with (runtime / 'server.log').open('wb') as log:
        process = subprocess.Popen([str(binary), 'serve'], env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(60):
        if process.poll() is not None:
            raise StageError('Local labeller server exited')
        try:
            with urllib.request.urlopen(LABELLER_URL + '/api/version', timeout=2) as response:
                if json.load(response).get('version') == VERSION.removeprefix('v'):
                    break
        except (OSError, ValueError):
            pass
        time.sleep(1)
    else:
        raise StageError('Local labeller server did not start')
    with (runtime / 'pull.log').open('wb') as log:
        subprocess.run([str(binary), 'pull', MODEL_NAME], env=env, stdout=log,
                       stderr=subprocess.STDOUT, timeout=900, check=True)
    verify_labeller()
    print('Pinned local labeller ready; cloud inference disabled')


if __name__ == '__main__':
    try:
        start()
    except (OSError, ValueError, subprocess.SubprocessError, StageError):
        raise SystemExit('Local labeller setup failed; no cloud fallback') from None
