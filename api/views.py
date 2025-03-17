from Bio import Entrez
from collections import Counter
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
import requests

Entrez.email = settings.ENTREZ_EMAIL


def home(request):
    return render(request, 'home.html')


def get_protein(request):
    protein_id = request.GET.get('id')
    print(f"Received protein_id: {protein_id}")
    if not protein_id:
        return JsonResponse({'error': 'Protein ID is required'}, status=400)

    try:
        handle = Entrez.efetch(db="protein", id=protein_id,
                               rettype="fasta", retmode="text")
        sequence = handle.read()
        handle.close()

        cleaned_sequence = ''.join(sequence.splitlines()[1:])
        analysis = analyze_sequence(cleaned_sequence)

        pdb_id = fetch_pdb_id_via_rcsb(cleaned_sequence)
        if not pdb_id:
            print(f"No PDB ID found for protein_id: {protein_id}")
            return JsonResponse({
                'error': 'PDB ID not found for the given protein ID.',
                'sequence': cleaned_sequence,
                'analysis': analysis,
                'pdb_id': None
            }, status=404)
        return JsonResponse({
            'sequence': cleaned_sequence,
            'analysis': analysis,
            'pdb_id': pdb_id
        })

    except Exception as e:
        print(f"Error occurred: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def analyze_sequence(sequence):
    cleaned_sequence = ''.join(sequence.split())
    amino_acid_count = Counter(cleaned_sequence)
    return dict(amino_acid_count)


def fetch_pdb_id_via_rcsb(sequence):
    try:
        print(f"Searching for PDB ID via RCSB PDB Search API...")
        url = "https://search.rcsb.org/rcsbsearch/v2/query"
        payload = {
            "query": {
                "type": "terminal",
                "service": "sequence",
                "parameters": {
                    "value": sequence,
                    "identity_cutoff": 0.9,
                    "evalue_cutoff": 0.1,
                    "sequence_type": "protein"
                }
            },
            "request_options": {
                "scoring_strategy": "sequence"
            },
            "return_type": "entry"
        }

        print(
            f"Sending request to RCSB PDB Search API with payload: {payload}")

        response = requests.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        print(f"Received response from RCSB PDB Search API: {data}")

        if data and data.get("result_set"):
            pdb_id = data["result_set"][0]["identifier"]
            print(f"Found PDB ID: {pdb_id}")
            return pdb_id.lower()
        else:
            print("No PDB ID found in RCSB PDB Search API response.")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching PDB ID via RCSB PDB Search API: {e}")
        print(f"Response content: {e.response.content}")
        return None
    except Exception as e:
        print(f"Error fetching PDB ID via RCSB PDB Search API: {e}")
        return None
