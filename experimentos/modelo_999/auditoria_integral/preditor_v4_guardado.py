"""V4.1: protecao de metadados e revisoes; formula V4 congelada preservada."""
from preditor_causal_v4 import predict,_time,_count
GUARD_VERSION='4.1'

def blocked(reason):
    return {'estimate_a':None,'lower_a':None,'upper_a':None,'conditional_winner':None,
            'probability':None,'remaining_electorate':None,'status':'ABSTAIN','reason':reason,
            'guard_version':GUARD_VERSION,'clear_prior_forecast':True}

def predict_guarded(current,reference,ledger,previous=None):
    """previous é o agregado current do snapshot anterior aceito.
    O integrador deve persistir estado e retirar previsoes anteriores em revisao.
    timestamp e cutoff de avaliacao; generated_at opcional identifica geracao.
    Ordem valida:generated_at<=available_at<=cutoff, quando geracao informada.
    Nao valida autenticidade de dados, nao antecipa revisao futura desconhecida.
    """
    try:
        now=_time(current['timestamp']);available=_time(current['available_at'])
        if available>now:return blocked('national_unavailable_at_cutoff')
        if current.get('generated_at') is not None and _time(current['generated_at'])>available:return blocked('national_received_before_generation')
        for k in ['votes_a','votes_b','electorate_total','electorate_counted']:_count(current[k])
        if previous is not None:
            prior_time=_time(previous['timestamp']);prior_available=_time(previous['available_at'])
            if prior_time>now:return blocked('out_of_order_national_snapshot')
            if prior_available>prior_time:return blocked('previous_clock_inconsistent')
            if previous.get('generated_at') is not None and _time(previous['generated_at'])>prior_available:return blocked('previous_clock_inconsistent')
            keys=['votes_a','votes_b','electorate_total','electorate_counted']
            for k in keys:_count(previous[k])
            if prior_time==now and any(previous[k]!=current[k] for k in keys):return blocked('conflicting_national_snapshot')
            if current['electorate_total']!=previous['electorate_total']:return blocked('electorate_registry_changed')
            if any(current[k]<previous[k] for k in ['votes_a','votes_b','electorate_counted']):return blocked('observed_counts_revised')
        out=predict(current,reference,ledger)
        return {**out,'guard_version':GUARD_VERSION,'clear_prior_forecast':out['estimate_a'] is None,
                'previous_snapshot_checked':previous is not None,'generation_time_provided':current.get('generated_at') is not None}
    except (ValueError,TypeError,AttributeError,KeyError,OverflowError):return blocked('invalid_input_contract')
