# -*- coding: utf-8 -*-

class CheatQuotas(object):
    # Liste statique des quotas (nombre de "Touchés" souhaités par tour de 4 tirs)
    # Progression logique : début prudent, montée en puissance, pic de triche, redescente et surprise.
    # Total : 1x0, 3x1, 3x2, 3x3, 1x4 = 11 tours
    QUOTAS = [0, 1, 3, 2, 1, 4, 2, 3, 1, 3, 2]

    def __init__(self):
        self.current_index = 0

    def get_next_quota(self):
        """Récupère le quota pour le tour suivant du bot."""
        if self.current_index < len(self.QUOTAS):
            quota = self.QUOTAS[self.current_index]
            self.current_index += 1
            return quota
        return 0 # Par défaut 0 si on dépasse les 11 tours

    def get_current_quota(self):
        """Récupère le quota du tour actuel sans avancer."""
        idx = max(0, self.current_index - 1)
        if idx < len(self.QUOTAS):
            return self.QUOTAS[idx]
        return 0

    def get_remaining_turns(self):
        return len(self.QUOTAS) - self.current_index
